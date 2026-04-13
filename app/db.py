import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "ride_requester_db")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set. Check your .env file.")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

drivers_collection = db["drivers"]
rides_collection = db["rides"]
metadata_collection = db["metadata"]