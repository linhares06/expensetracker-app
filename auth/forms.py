from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo

from auth.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', render_kw={'class': 'form-control'}, validators=[DataRequired()])
    password = PasswordField('Password', render_kw={'class': 'form-control'}, validators=[DataRequired()])
        
class RegisterForm(FlaskForm):
    username = StringField('Username', render_kw={'class': 'form-control'}, validators=[DataRequired()])
    password = PasswordField('Password', render_kw={'class': 'form-control'}, validators=[DataRequired()])
    confirm = PasswordField('Repeat password', render_kw={'class': 'form-control'}, validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
