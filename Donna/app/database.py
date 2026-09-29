from pymongo import MongoClient
from config import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client["mydb"]  # Get the default database from the URI

# Collections
contracts_collection = db["contracts"]
analysis_collection = db["analysis"]

def init_db():
    # Create indexes for the collections if they don't exist
    contracts_collection.create_index("filename", unique=True)
    analysis_collection.create_index("contract_id")