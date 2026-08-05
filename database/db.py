from pymongo import MongoClient
import os
import certifi
import gridfs

db = None
client = None
fs = None

def init_db(app):
    global db, client
    # In production, we'd use app.config['MONGO_URI']
    mongo_uri = app.config.get('MONGO_URI')
    if mongo_uri:
        client = MongoClient(mongo_uri, tlsCAFile=certifi.where(), tlsAllowInvalidCertificates=True)
        # Parse the database name from URI or default to 'online_course_registration'
        db = client.get_database('online_course_registration')
        fs = gridfs.GridFS(db)
        print("Connected to MongoDB and initialized GridFS successfully.")
    else:
        print("Warning: MONGO_URI not found in configuration.")

def get_db():
    return db

def get_fs():
    return fs
