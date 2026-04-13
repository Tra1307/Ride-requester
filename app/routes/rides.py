from fastapi import APIRouter, HTTPException
from app.models import RideRequest, RideCreate, Location, ModeUpdate
from app.state import set_mode, get_mode, NODE_ID
from app.services.assignment import assign_driver_to_ride
from app.services.replication import broadcast_to_peers
from app.db import rides_collection

router = APIRouter(prefix="/rides", tags=["Rides"])


def ride_to_mongo_doc(ride: RideRequest) -> dict:
    doc = ride.model_dump()
    doc["_id"] = ride.ride_id
    return doc


def mongo_doc_to_ride(doc: dict) -> RideRequest:
    doc = dict(doc)
    doc.pop("_id", None)
    return RideRequest(**doc)


@router.post("/")
async def create_ride(ride_data: RideCreate):
    existing_ride = rides_collection.find_one({"_id": ride_data.ride_id})
    if existing_ride:
        raise HTTPException(status_code=400, detail="Ride already exists")

    ride = RideRequest(
        ride_id=ride_data.ride_id,
        rider_name=ride_data.rider_name,
        pickup=Location(x=ride_data.pickup_x, y=ride_data.pickup_y),
        dropoff=Location(x=ride_data.dropoff_x, y=ride_data.dropoff_y)
    )

    rides_collection.insert_one(ride_to_mongo_doc(ride))
    await broadcast_to_peers("/internal/replicate/ride", ride.model_dump())

    return {"message": "Ride created", "ride": ride, "node": NODE_ID}


@router.get("/")
def list_rides():
    docs = list(rides_collection.find())
    rides = [mongo_doc_to_ride(doc) for doc in docs]
    return {"rides": rides, "node": NODE_ID}


@router.get("/{ride_id}")
def get_ride(ride_id: str):
    doc = rides_collection.find_one({"_id": ride_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Ride not found")
    return mongo_doc_to_ride(doc)


@router.post("/{ride_id}/assign")
async def assign_ride(ride_id: str):
    result = await assign_driver_to_ride(ride_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/{ride_id}/sync")
async def sync_ride_to_peers(ride_id: str):
    doc = rides_collection.find_one({"_id": ride_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Ride not found")

    ride = mongo_doc_to_ride(doc)
    await broadcast_to_peers("/internal/replicate/assignment", ride.model_dump())

    return {
        "message": f"Ride {ride_id} synced to peers",
        "ride": ride
    }


@router.put("/mode")
def update_mode(mode_data: ModeUpdate):
    set_mode(mode_data.mode)
    return {"message": f"System mode updated to {mode_data.mode}"}


@router.get("/mode/current")
def current_mode():
    return {"mode": get_mode()}