import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask
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



# Import routes
from . import views
from . import auth


app.register_blueprint(auth.auth_bp)