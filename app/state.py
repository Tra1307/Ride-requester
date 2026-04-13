import os
from app.models import ConsistencyMode

# -----------------------------
# System Mode (CP / AP)
# -----------------------------
system_mode: ConsistencyMode = ConsistencyMode.CP


def set_mode(mode: ConsistencyMode) -> None:
    global system_mode
    system_mode = mode


def get_mode() -> ConsistencyMode:
    return system_mode


# -----------------------------
# Node Configuration
# -----------------------------
NODE_ID = os.getenv("NODE_ID", "A")
PORT = int(os.getenv("PORT", "8000"))

PEERS = [
    peer.strip()
    for peer in os.getenv("PEERS", "").split(",")
    if peer.strip()
]


# -----------------------------
# Quorum Helpers (CP Mode)
# -----------------------------
def total_nodes() -> int:
    return 1 + len(PEERS)


def quorum_size() -> int:
    # Majority quorum
    return (total_nodes() // 2) + 1