from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

from auth.forms import LoginForm, RegisterForm
from auth.models import User, RegisterUser


bp = Blueprint('auth', __name__)

bcrypt = Bcrypt()

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.

    GET: Display the login form.
    POST: Validate the submitted form, log in the user if valid.

    Returns:
    redirect: Redirects to the home page after successful login.
    """
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('tracker.home'))
     
    form = LoginForm(request.form)
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.get_user(username=username)
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('tracker.home'))
        else:
            flash('Invalid username and/or password.', 'danger')
            return render_template('login.html', form=form)
        
    return render_template('login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.

    GET: Display the registration form.
    POST: Validate the submitted form, register the user if valid, and log in the user.

    Returns:
    redirect: Redirects to the home page after successful registration and login.
    """
    if current_user.is_authenticated:
        flash('You are already registered.', 'info')
        return redirect(url_for('tracker.home'))
    
    form = RegisterForm(request.form)

    if form.validate_on_submit():
        username = form.username.data
        password = bcrypt.generate_password_hash(form.password.data)

        if User.validate_unique_username(username=username):

            register_user = RegisterUser(username=username, password=password)

            #TODO: change return to user obj?
            user_id = register_user.save()
            
            user = User(_id=user_id, username=username, password=password)
            
            login_user(user)
            flash('You registered and are now logged in. Welcome!', 'success')

            return redirect(url_for('tracker.home'))
        
        flash('Username already submitted', 'info')

    return render_template('/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """
    Log out the current user.

    Logs out the user using the `logout_user` function, displays a success message,
    and redirects to the login page.

    Returns:
    redirect: Redirects to the login page after successful logout.
    """
    logout_user()
    flash('You were logged out.', 'success')
    return redirect(url_for('auth.login'))

