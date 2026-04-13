from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.routes import drivers, rides, internal
from app.state import NODE_ID, PEERS, PORT

app = FastAPI(title="Ride Requester Distributed Systems Demo")

app.include_router(drivers.router)
app.include_router(rides.router)
app.include_router(internal.router)


@app.get("/")
def root():
    return {
        "message": "Ride Requester API is running",
        "node": NODE_ID,
        "port": PORT,
        "peers": PEERS
    }