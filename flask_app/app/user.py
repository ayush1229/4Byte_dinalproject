from flask_login import UserMixin
from bson import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])  # MongoDB ObjectId to string
        self.username = user_data.get('username')
        self.role = user_data.get('role', 'user')