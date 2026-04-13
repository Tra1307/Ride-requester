from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class DriverStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class RideStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConsistencyMode(str, Enum):
    CP = "cp"
    AP = "ap"


class Location(BaseModel):
    x: float
    y: float


class Driver(BaseModel):
    driver_id: str
    name: str
    location: Location
    status: DriverStatus = DriverStatus.AVAILABLE


class DriverCreate(BaseModel):
    driver_id: str
    name: str
    x: float
    y: float


class RideRequest(BaseModel):
    ride_id: str
    rider_name: str
    pickup: Location
    dropoff: Location
    status: RideStatus = RideStatus.PENDING
    assigned_driver_id: Optional[str] = None
    timestamp: Optional[str] = None
    version: int = 1


class RideCreate(BaseModel):
    ride_id: str
    rider_name: str
    pickup_x: float
    pickup_y: float
    dropoff_x: float
    dropoff_y: float


class ModeUpdate(BaseModel):
    mode: ConsistencyMode


class AssignmentProposal(BaseModel):
    ride_id: str
    driver_id: str


class VoteResponse(BaseModel):
    approve: bool
    node: str
    reason: str
