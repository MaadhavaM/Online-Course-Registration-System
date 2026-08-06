from flask import Flask, render_template, redirect, url_for, send_file, abort
from flask_login import LoginManager, current_user
from config import Config
from database.db import init_db, get_fs
from models.user import get_user_by_id
from bson.objectid import ObjectId
import io

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize MongoDB
    init_db(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.instructor import instructor_bp
    from routes.student import student_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(instructor_bp, url_prefix='/instructor')
    app.register_blueprint(student_bp, url_prefix='/student')

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == 'instructor':
                return redirect(url_for('instructor.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        return render_template('index.html')

    @app.route('/download/<file_id>')
    def download_file(file_id):
        fs = get_fs()
        try:
            grid_out = fs.get(ObjectId(file_id))
            return send_file(
                io.BytesIO(grid_out.read()),
                mimetype=grid_out.content_type,
                as_attachment=True,
                download_name=grid_out.filename
            )
        except Exception as e:
            print(f"Error downloading file: {e}")
            abort(404)

    @app.route('/view_file_raw/<file_id>')
    def view_file_raw(file_id):
        fs = get_fs()
        try:
            grid_out = fs.get(ObjectId(file_id))
            return send_file(
                io.BytesIO(grid_out.read()),
                mimetype=grid_out.content_type,
                as_attachment=False,
                download_name=grid_out.filename
            )
        except Exception as e:
            print(f"Error viewing file: {e}")
            abort(404)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
