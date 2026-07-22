# UniCore - Online Course Registration System

UniCore is a comprehensive, web-based Online Course Registration System built with Python, Flask, and MongoDB. It provides dedicated portals for Students, Instructors, and Administrators to streamline the academic registration and management process.

## 🌟 Features

### 🎓 For Students
* **Account Registration:** Self-service registration for new students.
* **Course Browsing:** Browse available courses by department and category.
* **Enrollment Management:** Enroll in active courses and track enrollment status (Registered/Completed).
* **Dashboard:** View a personalized dashboard with total enrollments, active courses, and registration dates.

### 👨‍🏫 For Instructors
* **Course Management:** Create, manage, and track courses assigned to them.
* **Student Tracking:** View a detailed list of all students enrolled in their courses.
* **Assignments:** Upload and manage course materials and assignments for enrolled students.
* **Dashboard:** Track total students, active courses, and assignment metrics at a glance.

### 🛡️ For Administrators
* **Centralized Dashboard:** View high-level metrics (total students, instructors, courses, enrollments).
* **User Management:** Create and provision Instructor accounts (students self-register).
* **System Management:** Add and manage Departments and Course Categories.
* **Data Export:** Export student records to CSV for external processing.

## 🛠️ Technology Stack

* **Backend:** Python 3, Flask
* **Database:** MongoDB (via PyMongo)
* **Authentication:** Flask-Login, Werkzeug Security (Password Hashing)
* **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2 Templating
* **Environment Management:** python-dotenv

## 🚀 Getting Started

### Prerequisites
* Python 3.8+
* MongoDB database (local or cloud like MongoDB Atlas)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MaadhavaM/Online-Course-Registration-System.git
   cd Online-Course-Registration-System
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   Create a `.env` file in the root directory and add your secret key and MongoDB URI:
   ```env
   SECRET_KEY=your_secure_secret_key_here
   MONGO_URI=mongodb://localhost:27017/  # Or your MongoDB Atlas connection string
   ```

5. **Initialize the Database:**
   Run the initialization script to create the default Admin account and system categories:
   ```bash
   python init_db.py
   ```
   *(Creates default Admin: `admin@example.com` / `admin123`)*

6. **Seed Mock Data (Optional):**
   To populate the database with a mock instructor and sample courses, run:
   ```bash
   python seed_courses.py
   ```
   *(Creates mock Instructor: `alan.turing@example.com` / `password123`)*

7. **Run the Application:**
   ```bash
   python app.py
   ```
   The application will be accessible at `http://127.0.0.1:5000/`.

## 🔒 Default Credentials

If you ran the initialization scripts, you can log in with:

* **Admin:** `admin@example.com` | Password: `admin123`
* **Instructor:** `alan.turing@example.com` | Password: `password123`

*(Note: Please change these passwords in a production environment!)*

## 📄 License
This project is open-source and available for educational and personal use.
