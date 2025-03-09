from flask import Flask
from flask_login import LoginManager
from flask_pymongo import PyMongo
from bson import ObjectId
from .config import Config
from .user import User

login_manager = LoginManager()
mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'

    @login_manager.user_loader
    def load_user(user_id):
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(str(user_data['_id']), user_data['username'], user_data['role'])
        return None

    from .routes.admin_routes import admin_bp
    from .routes.voter_routes import voter_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(voter_bp)

    with app.app_context():
        mongo.db.voter_ids.create_index([("voter_id", 1)], unique=True)

    return app