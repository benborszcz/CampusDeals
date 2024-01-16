import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'asoifboiasfopbasopdbfou[asbo[d]]'

# Initialize Firebase Admin SDK
cred = credentials.Certificate('app/firebase_service_account.json')
firebase_admin.initialize_app(cred)

# Initialize Firestore instance
db = firestore.client()

# Import routes
from . import views