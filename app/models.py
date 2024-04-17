from flask_login import UserMixin
from flask_login import LoginManager

login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, user_id, username = None, email = None, profile_picture_url = None):
        self.id = user_id
        self.email = email
        self.username = username if username else email
        self.profile_picture_url = profile_picture_url if profile_picture_url else 'static/images/default_profile.png'

    @classmethod
    def create_or_update_from_auth0(cls, userinfo):
        # import within function to avoid circular import 
        from app import db
        # Extract necessary information from userinfo
        user_id = userinfo['sub']  # Auth0 user ID
        email = userinfo.get('email')
        username = userinfo.get('nickname', email)  # Use nickname or fall back to email
        
        # Query database to find an existing user by their Auth0 ID
        user_ref = db.collection('users').document(user_id)
        doc = user_ref.get()

        if doc.exists: 
            # If the user exists, update their info
            user_ref.update({
                'email': email,
                'username': username,
            })
            user = cls(user_id, email=email, username=username)
        else:
            # If the user doesn't exist, create a new instance and save it
            user_ref.set({
                'id': user_id,
                'email': email,
                'username': username,
            })
            user = cls(user_id, email, username)        
        return user

@login_manager.user_loader
def load_user(user_id):
    from app import db 
    user_ref = db.collection('users').document(user_id)
    doc = user_ref.get()
    if doc.exists:
        user_data = doc.to_dict()
        return User(user_id, user_data.get('username'), user_data.get('email'))
    return None