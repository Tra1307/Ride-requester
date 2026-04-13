from fastapi import APIRouter, HTTPException
from app.models import Driver, DriverCreate, Location, DriverStatus
from app.state import NODE_ID, PEERS
from app.services.replication import broadcast_to_peers
from app.db import drivers_collection

router = APIRouter(prefix="/drivers", tags=["Drivers"])


def driver_to_mongo_doc(driver: Driver) -> dict:
    doc = driver.model_dump()
    doc["_id"] = driver.driver_id
    return doc


def mongo_doc_to_driver(doc: dict) -> Driver:
    doc = dict(doc)
    doc.pop("_id", None)
    return Driver(**doc)


@router.post("/")
async def create_driver(driver_data: DriverCreate):
    existing_driver = drivers_collection.find_one({"_id": driver_data.driver_id})
    if existing_driver:
        raise HTTPException(status_code=400, detail="Driver already exists")

    driver = Driver(
        driver_id=driver_data.driver_id,
        name=driver_data.name,
        location=Location(x=driver_data.x, y=driver_data.y),
        status=DriverStatus.AVAILABLE
    )

    drivers_collection.insert_one(driver_to_mongo_doc(driver))

    await broadcast_to_peers("/internal/replicate/driver", driver.model_dump())

    return {
        "message": "Driver created",
        "driver": driver,
        "node": NODE_ID,
        "peers": PEERS
    }


@router.get("/")
def list_drivers():
    docs = list(drivers_collection.find())
    drivers = [mongo_doc_to_driver(doc) for doc in docs]
    return {"drivers": drivers, "node": NODE_ID}


@router.get("/{driver_id}")
def get_driver(driver_id: str):
    doc = drivers_collection.find_one({"_id": driver_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Driver not found")

    return mongo_doc_to_driver(doc)


@router.put("/{driver_id}/available")
async def mark_driver_available(driver_id: str):
    doc = drivers_collection.find_one({"_id": driver_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Driver not found")

    driver = mongo_doc_to_driver(doc)
    driver.status = DriverStatus.AVAILABLE

    drivers_collection.replace_one(
        {"_id": driver_id},
        driver_to_mongo_doc(driver)
    )

    await broadcast_to_peers("/internal/replicate/driver", driver.model_dump())

    return {"message": f"Driver {driver_id} marked available", "driver": driver}


@router.put("/{driver_id}/offline")
async def mark_driver_offline(driver_id: str):
    doc = drivers_collection.find_one({"_id": driver_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Driver not found")

    driver = mongo_doc_to_driver(doc)
    driver.status = DriverStatus.OFFLINE

    drivers_collection.replace_one(
        {"_id": driver_id},
        driver_to_mongo_doc(driver)
    )

    await broadcast_to_peers("/internal/replicate/driver", driver.model_dump())

    return {"message": f"Driver {driver_id} marked offline", "driver": driver}