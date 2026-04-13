from math import sqrt
from datetime import datetime
from app.models import (
    Driver,
    RideRequest,
    DriverStatus,
    RideStatus,
    ConsistencyMode,
    AssignmentProposal,
)
from app.state import get_mode, quorum_size, NODE_ID
from app.services.replication import broadcast_to_peers, request_votes_from_peers
from app.db import drivers_collection, rides_collection


def driver_to_mongo_doc(driver: Driver) -> dict:
    doc = driver.model_dump()
    doc["_id"] = driver.driver_id
    return doc


def mongo_doc_to_driver(doc: dict) -> Driver:
    doc = dict(doc)
    doc.pop("_id", None)
    return Driver(**doc)


def ride_to_mongo_doc(ride: RideRequest) -> dict:
    doc = ride.model_dump()
    doc["_id"] = ride.ride_id
    return doc


def mongo_doc_to_ride(doc: dict) -> RideRequest:
    doc = dict(doc)
    doc.pop("_id", None)
    return RideRequest(**doc)


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def find_nearest_available_driver(ride: RideRequest) -> Driver | None:
    available_driver_docs = list(drivers_collection.find({"status": DriverStatus.AVAILABLE.value}))
    available_drivers = [mongo_doc_to_driver(doc) for doc in available_driver_docs]

    if not available_drivers:
        return None

    return min(
        available_drivers,
        key=lambda d: distance(
            d.location.x,
            d.location.y,
            ride.pickup.x,
            ride.pickup.y
        )
    )


async def assign_driver_to_ride(ride_id: str):
    ride_doc = rides_collection.find_one({"_id": ride_id})
    if not ride_doc:
        return {"error": "Ride not found"}

    ride = mongo_doc_to_ride(ride_doc)

    if ride.status != RideStatus.PENDING:
        return {"error": f"Ride cannot be assigned because it is {ride.status}"}

    driver = find_nearest_available_driver(ride)
    if driver is None:
        return {"message": "No available driver found", "ride": ride}

    mode = get_mode()

    # -------------------------
    # CP MODE
    # -------------------------
    if mode == ConsistencyMode.CP:
        proposal = AssignmentProposal(
            ride_id=ride.ride_id,
            driver_id=driver.driver_id
        )

        approvals = 1
        votes = [{
            "approve": True,
            "node": NODE_ID,
            "reason": "leader approved locally"
        }]

        peer_votes = await request_votes_from_peers(
            "/internal/prepare-assignment",
            proposal.model_dump()
        )

        votes.extend(peer_votes)

        for vote in peer_votes:
            if vote.get("approve") is True:
                approvals += 1

        needed = quorum_size()

        if approvals < needed:
            return {
                "message": "CP mode: quorum not reached, assignment rejected",
                "ride": ride,
                "proposed_driver_id": driver.driver_id,
                "approvals": approvals,
                "quorum_required": needed,
                "votes": votes
            }

        driver.status = DriverStatus.BUSY
        ride.status = RideStatus.ASSIGNED
        ride.assigned_driver_id = driver.driver_id
        ride.timestamp = datetime.utcnow().isoformat()
        ride.version += 1

        drivers_collection.replace_one(
            {"_id": driver.driver_id},
            driver_to_mongo_doc(driver),
            upsert=True
        )
        rides_collection.replace_one(
            {"_id": ride.ride_id},
            ride_to_mongo_doc(ride),
            upsert=True
        )

        await broadcast_to_peers("/internal/replicate/driver", driver.model_dump())
        await broadcast_to_peers("/internal/replicate/assignment", ride.model_dump())

        return {
            "message": "CP mode: quorum reached, assignment committed",
            "ride": ride,
            "driver": driver,
            "approvals": approvals,
            "quorum_required": needed,
            "votes": votes
        }

    # -------------------------
    # AP MODE
    # -------------------------
    driver.status = DriverStatus.BUSY
    ride.status = RideStatus.ASSIGNED
    ride.assigned_driver_id = driver.driver_id
    ride.timestamp = datetime.utcnow().isoformat()
    ride.version += 1

    drivers_collection.replace_one(
        {"_id": driver.driver_id},
        driver_to_mongo_doc(driver),
        upsert=True
    )
    rides_collection.replace_one(
        {"_id": ride.ride_id},
        ride_to_mongo_doc(ride),
        upsert=True
    )

    await broadcast_to_peers("/internal/replicate/driver", driver.model_dump())
    await broadcast_to_peers("/internal/replicate/assignment", ride.model_dump())

    return {
        "message": "AP mode: assignment committed locally; peers will catch up later",
        "ride": ride,
        "driver": driver,
        "node": NODE_ID
    }