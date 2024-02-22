from flask import Blueprint, render_template, redirect, url_for, flash, get_flashed_messages, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import User, login_manager  # Import User directly from models, not from . (avoiding circular import)
import os
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import url_for, redirect, session, request

load_dotenv()

auth_bp = Blueprint('auth', __name__)

class RegistrationForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired(), validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.DataRequired(), validators.Email()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'),
        validators.Length(min=6)
    ])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Register')

    def validate_email(form, field):
        # Custom validation for email
        user_ref = db.collection('users').where('email', '==', field.data).limit(1).get()
        if user_ref:
            raise validators.ValidationError('Email is already in use.')

class LoginForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
    submit = SubmitField('Login')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Check if the email is already taken
        email_ref = db.collection('users').where('email', '==', email).limit(1).get()
        if email_ref:
            flash('Email is already in use. Please use a different email.', 'danger')
            return redirect(url_for('auth.register'))

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
            'email': email,
            'password': hashed_password
        })

        flash('Account created successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    get_flashed_messages()
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
                email = user_data.to_dict()['email']
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Incorrect password. Please try again.', 'danger')
        else:
            flash('Username not found. Please register.', 'danger')

    get_flashed_messages()
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    #flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/auth0-login')
def auth0_login():
    auth0 = current_app.config['AUTH0']
    redirect_uri = url_for('auth.auth0_callback', _external=True)
    result = auth0.authorize_redirect(redirect_uri=redirect_uri)
    return result

@auth_bp.route('/auth0-callback')
def auth0_callback():
    auth0 = current_app.config['AUTH0']
    try:
        token = auth0.authorize_access_token()
    except Exception as e:
        print(e)
        print('no token!')
        return redirect(url_for('auth.login'))
    resp = auth0.get('userinfo')
    userinfo = resp.json()
    
    # Adjusted to use your custom User class method for creating or updating users
    user = User.create_or_update_from_auth0(userinfo)
    
    if user:
        print('Found user!')
        login_user(user)
        return redirect(url_for('index'))
    else:
        print('No user!')
        # Handle error or failed user creation/login
        return redirect(url_for('auth.login'))

def configure_auth(app, oauth):
    auth0 = oauth.register(
    'auth0',
    client_id=os.getenv('AUTH0_CLIENT_ID'),
    client_secret=os.getenv('AUTH0_CLIENT_SECRET'),
    api_base_url='https://'+os.getenv('AUTH0_DOMAIN'),
    access_token_url='https://'+os.getenv('AUTH0_DOMAIN')+'/oauth/token',
    authorize_url='https://'+os.getenv('AUTH0_DOMAIN')+'/authorize',
    client_kwargs={'scope': 'openid profile email'},
    jwks_uri='https://'+os.getenv('AUTH0_DOMAIN')+'/.well-known/jwks.json'
    )
    app.config['AUTH0'] = auth0
    return auth0