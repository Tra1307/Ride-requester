from fastapi import APIRouter
from app.models import Driver, RideRequest, AssignmentProposal, VoteResponse, DriverStatus, RideStatus
from app.state import NODE_ID
from app.services.conflict_resolution import choose_winning_ride
from app.db import drivers_collection, rides_collection

router = APIRouter(prefix="/internal", tags=["Internal"])


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


@router.post("/replicate/driver")
def replicate_driver(driver: Driver):
    drivers_collection.replace_one(
        {"_id": driver.driver_id},
        driver_to_mongo_doc(driver),
        upsert=True
    )
    return {"message": f"Driver {driver.driver_id} replicated"}


@router.post("/replicate/ride")
def replicate_ride(incoming_ride: RideRequest):
    existing_doc = rides_collection.find_one({"_id": incoming_ride.ride_id})

    if not existing_doc:
        rides_collection.insert_one(ride_to_mongo_doc(incoming_ride))
        return {"message": f"Ride {incoming_ride.ride_id} replicated (new)"}

    local_ride = mongo_doc_to_ride(existing_doc)
    winner = choose_winning_ride(local_ride, incoming_ride)

    rides_collection.replace_one(
        {"_id": winner.ride_id},
        ride_to_mongo_doc(winner),
        upsert=True
    )

    if winner.assigned_driver_id:
        winning_driver_doc = drivers_collection.find_one({"_id": winner.assigned_driver_id})
        if winning_driver_doc:
            winning_driver = mongo_doc_to_driver(winning_driver_doc)
            winning_driver.status = DriverStatus.BUSY
            drivers_collection.replace_one(
                {"_id": winning_driver.driver_id},
                driver_to_mongo_doc(winning_driver),
                upsert=True
            )

    return {
        "message": f"Ride {incoming_ride.ride_id} reconciled",
        "winning_driver_id": winner.assigned_driver_id,
        "version": winner.version
    }


@router.post("/replicate/assignment")
def replicate_assignment(incoming_ride: RideRequest):
    existing_doc = rides_collection.find_one({"_id": incoming_ride.ride_id})

    if not existing_doc:
        winner = incoming_ride
    else:
        local_ride = mongo_doc_to_ride(existing_doc)
        winner = choose_winning_ride(local_ride, incoming_ride)

    rides_collection.replace_one(
        {"_id": winner.ride_id},
        ride_to_mongo_doc(winner),
        upsert=True
    )

    if winner.assigned_driver_id:
        driver_doc = drivers_collection.find_one({"_id": winner.assigned_driver_id})
        if driver_doc:
            driver = mongo_doc_to_driver(driver_doc)
            driver.status = DriverStatus.BUSY
            drivers_collection.replace_one(
                {"_id": driver.driver_id},
                driver_to_mongo_doc(driver),
                upsert=True
            )

    return {
        "message": f"Assignment for ride {incoming_ride.ride_id} processed",
        "winning_driver_id": winner.assigned_driver_id,
        "version": winner.version
    }


@router.post("/prepare-assignment", response_model=VoteResponse)
def prepare_assignment(proposal: AssignmentProposal):
    ride_doc = rides_collection.find_one({"_id": proposal.ride_id})
    if not ride_doc:
        return VoteResponse(
            approve=False,
            node=NODE_ID,
            reason="ride not found"
        )

    driver_doc = drivers_collection.find_one({"_id": proposal.driver_id})
    if not driver_doc:
        return VoteResponse(
            approve=False,
            node=NODE_ID,
            reason="driver not found"
        )

    ride = mongo_doc_to_ride(ride_doc)
    driver = mongo_doc_to_driver(driver_doc)

    if ride.status != RideStatus.PENDING:
        return VoteResponse(
            approve=False,
            node=NODE_ID,
            reason=f"ride is {ride.status}"
        )

    if driver.status != DriverStatus.AVAILABLE:
        return VoteResponse(
            approve=False,
            node=NODE_ID,
            reason=f"driver is {driver.status}"
        )

    return VoteResponse(
        approve=True,
        node=NODE_ID,
        reason="approved"
    )