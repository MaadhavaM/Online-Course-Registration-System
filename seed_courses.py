import os
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

def seed_courses():
    load_dotenv()
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print("MONGO_URI not found!")
        return

    client = MongoClient(mongo_uri)
    db = client.get_database('online_course_registration')

    # Ensure there's at least one instructor
    instructor_collection = db.instructors
    instructor = instructor_collection.find_one({})
    if not instructor:
        print("No instructor found. Creating a mock instructor...")
        instructor_id = "INST001"
        instructor_data = {
            "instructor_id": instructor_id,
            "name": "Dr. Alan Turing",
            "email": "alan.turing@example.com",
            "phone": "1234567890",
            "department": "Computer Science",
            "password": generate_password_hash("password123"),
            "role": "instructor"
        }
        instructor_collection.insert_one(instructor_data)
        print("Created mock instructor (INST001 / password123)")
    else:
        instructor_id = instructor.get('instructor_id')
        print(f"Using existing instructor ID: {instructor_id}")

    # Generate mock courses
    mock_courses = [
        {
            "course_code": "CS101",
            "course_name": "Introduction to Computer Science",
            "description": "A comprehensive introduction to programming and computer science concepts.",
            "department": "Computer Science",
            "category": "Programming",
            "credits": 4,
            "duration": "16 weeks",
            "capacity": 100,
            "instructor_id": instructor_id,
            "status": "Active"
        },
        {
            "course_code": "CS201",
            "course_name": "Data Structures and Algorithms",
            "description": "Learn advanced data structures and algorithmic thinking.",
            "department": "Computer Science",
            "category": "Programming",
            "credits": 4,
            "duration": "16 weeks",
            "capacity": 80,
            "instructor_id": instructor_id,
            "status": "Active"
        },
        {
            "course_code": "DS101",
            "course_name": "Introduction to Data Science",
            "description": "Fundamentals of data science, statistics, and data visualization.",
            "department": "Computer Science",
            "category": "Data Science",
            "credits": 3,
            "duration": "12 weeks",
            "capacity": 120,
            "instructor_id": instructor_id,
            "status": "Active"
        },
        {
            "course_code": "CYB101",
            "course_name": "Fundamentals of Cybersecurity",
            "description": "Understand the basics of network security, cryptography, and ethical hacking.",
            "department": "Information Technology",
            "category": "Cybersecurity",
            "credits": 3,
            "duration": "14 weeks",
            "capacity": 60,
            "instructor_id": instructor_id,
            "status": "Active"
        },
        {
            "course_code": "IT102",
            "course_name": "Web Development Bootcamp",
            "description": "Build responsive and dynamic websites using modern web technologies.",
            "department": "Information Technology",
            "category": "Programming",
            "credits": 4,
            "duration": "12 weeks",
            "capacity": 150,
            "instructor_id": instructor_id,
            "status": "Active"
        },
        {
            "course_code": "EE201",
            "course_name": "Digital Logic Design",
            "description": "Design and analyze digital circuits and systems.",
            "department": "Electrical Engineering",
            "category": "Hardware",
            "credits": 4,
            "duration": "16 weeks",
            "capacity": 70,
            "instructor_id": instructor_id,
            "status": "Active"
        },
        {
            "course_code": "ME101",
            "course_name": "Engineering Mechanics",
            "description": "Fundamentals of statics and dynamics for engineering systems.",
            "department": "Mechanical Engineering",
            "category": "Engineering",
            "credits": 3,
            "duration": "14 weeks",
            "capacity": 90,
            "instructor_id": instructor_id,
            "status": "Active"
        },
        {
            "course_code": "DS202",
            "course_name": "Machine Learning Foundations",
            "description": "Introduction to predictive modeling, classification, and clustering techniques.",
            "department": "Computer Science",
            "category": "Data Science",
            "credits": 4,
            "duration": "16 weeks",
            "capacity": 65,
            "instructor_id": instructor_id,
            "status": "Active"
        },
        {
            "course_code": "DES101",
            "course_name": "UI/UX Design Principles",
            "description": "Learn how to design intuitive, beautiful, and user-centric interfaces.",
            "department": "Information Technology",
            "category": "Design",
            "credits": 3,
            "duration": "10 weeks",
            "capacity": 50,
            "instructor_id": instructor_id,
            "status": "Active"
        },
        {
            "course_code": "CS305",
            "course_name": "Cloud Computing Architecture",
            "description": "Explore the deployment and management of cloud-based applications.",
            "department": "Computer Science",
            "category": "Programming",
            "credits": 4,
            "duration": "14 weeks",
            "capacity": 75,
            "instructor_id": instructor_id,
            "status": "Active"
        }
    ]

    # Insert only if course_code doesn't exist
    courses_added = 0
    for course in mock_courses:
        if not db.courses.find_one({"course_code": course["course_code"]}):
            db.courses.insert_one(course)
            courses_added += 1

    print(f"Successfully added {courses_added} new courses for students to register!")

if __name__ == '__main__':
    seed_courses()
