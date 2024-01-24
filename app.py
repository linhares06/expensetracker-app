import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, flash
from flask_login import LoginManager

from tracker.routes import bp as tracker_bp
from auth.routes import bp as auth_bp
from auth.models import User


app = Flask(__name__)

load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)

app.register_blueprint(tracker_bp)
app.register_blueprint(auth_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id=user_id)

@login_manager.unauthorized_handler
def unauthorized():
    flash('Please login.')
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(port=8000, debug=True)