from flask import Blueprint, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User, login_manager  # Import User directly from models, not from . (avoiding circular import)

auth_bp = Blueprint('auth', __name__)

class RegistrationForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired(), validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'),
        validators.Length(min=6)
    ])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
    submit = SubmitField('Login')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Check if the username is already taken
        user_ref = db.collection('users').document(username)
        if user_ref.get().exists:
            flash('Username already taken. Please choose another.', 'danger')
            return redirect(url_for('auth.register'))

        # Hash the password before storing it
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Create a new user document in Firestore
        user_ref.set({
            'username': username,
            'password': hashed_password
        })

        flash('Account created successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Retrieve the user document from Firestore
        user_ref = db.collection('users').document(username)
        user_data = user_ref.get()

        if user_data.exists:
            # Check if the entered password matches the stored hashed password
            if check_password_hash(user_data.to_dict()['password'], password):
                user = User(user_id=username, username=username)
                login_user(user)
                flash('Login successful!', 'success')
                # Implement login logic here (e.g., session management)
                return redirect(url_for('index'))
            else:
                flash('Incorrect password. Please try again.', 'danger')
        else:
            flash('Username not found. Please register.', 'danger')

    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required  # This ensures that only logged-in users can access this route
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))
