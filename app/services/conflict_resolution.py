from datetime import datetime
from app.models import RideRequest, RideStatus


def parse_ts(ts: str | None) -> datetime:
    if not ts:
        return datetime.max
    return datetime.fromisoformat(ts)


def choose_winning_ride(local_ride: RideRequest, incoming_ride: RideRequest) -> RideRequest:
    """
    Winner rule:
    1. Assigned beats pending
    2. Earlier timestamp wins
    3. If tie, smaller driver_id wins
    4. If still tie, higher version wins
    """
    if local_ride.status != RideStatus.ASSIGNED and incoming_ride.status == RideStatus.ASSIGNED:
        return incoming_ride

    if local_ride.status == RideStatus.ASSIGNED and incoming_ride.status != RideStatus.ASSIGNED:
        return local_ride

    local_ts = parse_ts(local_ride.timestamp)
    incoming_ts = parse_ts(incoming_ride.timestamp)

    if incoming_ts < local_ts:
        return incoming_ride
    if local_ts < incoming_ts:
        return local_ride

    local_driver = local_ride.assigned_driver_id or "ZZZZZZ"
    incoming_driver = incoming_ride.assigned_driver_id or "ZZZZZZ"

    if incoming_driver < local_driver:
        return incoming_ride
    if local_driver < incoming_driver:
        return local_ride

    if incoming_ride.version > local_ride.version:
        return incoming_ride

    return local_ride
