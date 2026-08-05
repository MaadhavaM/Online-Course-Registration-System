import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

load_dotenv()
mongo_uri = os.getenv('MONGO_URI')

print(f"Connecting to: {mongo_uri}")
try:
    # Try with certifi
    client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
    client.admin.command('ping')
    print("Ping successful with certifi!")
except Exception as e:
    print(f"Error with certifi: {e}")

try:
    # Try without certifi but with tlsAllowInvalidCertificates
    client = MongoClient(mongo_uri, tlsAllowInvalidCertificates=True)
    client.admin.command('ping')
    print("Ping successful with tlsAllowInvalidCertificates=True!")
except Exception as e:
    print(f"Error with tlsAllowInvalidCertificates: {e}")
