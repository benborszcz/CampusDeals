import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask
from authlib.integrations.flask_client import OAuth
from .models import login_manager  


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'asoifboiasfopbasopdbfou[asbo[d]]'

# Initialize Firebase Admin SDK
cred = credentials.Certificate('app/firebase_service_account.json')
firebase_admin.initialize_app(cred)

# Initialize Firestore instance
db = firestore.client()

# Initialize Flask-Login
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Initialize Auth0
oauth = OAuth(app)

from .auth import configure_auth, auth_bp

auth0 = configure_auth(app, oauth)

app.config['AUTH0'] = auth0

# Import routes
from . import views
from . import auth


app.register_blueprint(auth.auth_bp)