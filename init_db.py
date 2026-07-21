from werkzeug.security import generate_password_hash
from pymongo import MongoClient
import os
from dotenv import load_dotenv

def initialize_database():
    load_dotenv()
    mongo_uri = os.getenv('MONGO_URI')
    
    if not mongo_uri:
        print("Error: MONGO_URI not found in environment.")
        return

    client = MongoClient(mongo_uri)
    db = client.get_database('online_course_registration')

    # Create initial admin
    admin_collection = db.admins
    if admin_collection.count_documents({}) == 0:
        admin_data = {
            "username": "admin",
            "email": "admin@example.com",
            "password": generate_password_hash("admin123"),
            "role": "admin"
        }
        admin_collection.insert_one(admin_data)
        print("Created default admin user (admin / admin123).")
    else:
        print("Admin user already exists.")

    # Create default departments
    dept_collection = db.departments
    if dept_collection.count_documents({}) == 0:
        departments = [
            {"name": "Computer Science"},
            {"name": "Information Technology"},
            {"name": "Electrical Engineering"},
            {"name": "Mechanical Engineering"}
        ]
        dept_collection.insert_many(departments)
        print("Created default departments.")
        
    # Create default categories
    cat_collection = db.categories
    if cat_collection.count_documents({}) == 0:
        categories = [
            {"name": "Programming"},
            {"name": "Data Science"},
            {"name": "Cybersecurity"},
            {"name": "Design"}
        ]
        cat_collection.insert_many(categories)
        print("Created default categories.")

if __name__ == '__main__':
    initialize_database()
