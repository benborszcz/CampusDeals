from flask_login import UserMixin
from flask_login import LoginManager


login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, user_id, username, email=None, birthday=None, college_class=None):
        self.id = user_id
        self.email = email
        self.username = username
        self.birthday = birthday
        self.college_class = college_class

@login_manager.user_loader
def load_user(user_id):
    # This function is required by Flask-Login to load a user from the user ID.
    # It should return None if the user ID is not valid.
    return User(user_id, None)
