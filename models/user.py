from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db

class User(UserMixin):
    def __init__(self, user_data, role):
        self.user_data = user_data
        self.role = role
        # We need an id attribute for Flask-Login
        if role == 'admin':
            self.id = str(user_data.get('_id'))
        elif role == 'instructor':
            self.id = user_data.get('instructor_id')
        elif role == 'student':
            self.id = user_data.get('student_id')
        else:
            self.id = str(user_data.get('_id'))

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return f"{self.role}:{self.id}"

def get_user_by_id(user_id_string):
    db = get_db()
    if db is None:
        return None
    
    try:
        role, u_id = user_id_string.split(':', 1)
    except ValueError:
        return None
    
    if role == 'admin':
        from bson.objectid import ObjectId
        try:
            user_data = db.admins.find_one({"_id": ObjectId(u_id)})
            if user_data:
                return User(user_data, 'admin')
        except:
            return None
    elif role == 'instructor':
        user_data = db.instructors.find_one({"instructor_id": u_id})
        if user_data:
            return User(user_data, 'instructor')
    elif role == 'student':
        user_data = db.students.find_one({"student_id": u_id})
        if user_data:
            return User(user_data, 'student')
            
    return None

def verify_password(stored_hash, provided_password):
    return check_password_hash(stored_hash, provided_password)
