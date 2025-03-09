from flask_login import UserMixin
from app import login_manager

class User(UserMixin):
    def __init__(self, user_id, role='user'):
        self.id = user_id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    # Simple demo implementation
    if user_id == 'admin':
        return User(user_id='admin', role='admin')
    return None