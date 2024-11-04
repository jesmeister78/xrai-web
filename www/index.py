# Reorganize imports in index.py
from flask import Flask, jsonify, redirect, request, url_for
from flask_login import LoginManager, login_required
import logging
import os
from flask_jwt_extended import (
    JWTManager
)
from datetime import timedelta

# local imports
from domain import db
from domain.exceptions import UserAlreadyExistsError
from www import error_handler

from www.config.auth_config import JWT_SECRET, jwt_blocklist
from services import user_service_ext

# configure the web app

app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')
app.secret_key = 'whyneedthiskeyla'
app.config.from_pyfile(os.path.join(".", "config/app.conf"), silent=False)
app.logger.setLevel(logging.INFO)

# Import routes
from www.config.auth_config import JWT_SECRET
from www.routes import account, users, procedures, images

# Inject services
user_service = user_service_ext.user_service

# init the login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'account.login'
    
# User loader function
@login_manager.user_loader
def load_user(user_id):
    return user_service.get_user_by_id(user_id)

# Setup Flask-JWT-Extended
app.config["JWT_SECRET_KEY"] = JWT_SECRET  
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
jwt = JWTManager(app)

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return user_service.get_user_by_id(identity)
    # return users_db.get(identity)

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in jwt_blocklist    
# Register a callback to add claims to the JWT - out of scope for now but we will need this for prod
# @jwt.additional_claims_loader
# def add_claims_to_jwt(identity):
#     return {
#         "roles": users_db[identity]["roles"]
#     }  

# set the custom error handler
error_handler = error_handler.ErrorHandler()

# Register routes from other files 
app.register_blueprint(account.blueprint) 
app.register_blueprint(users.blueprint) 
app.register_blueprint(procedures.blueprint)
app.register_blueprint(images.blueprint)

# -----------------------------------------------------------

# configure the database
db.init_app(app)

# create the tables (tables are not updated if they already exist in db. we will remove this statement once schema is stable)
with app.app_context():
    db.create_all()
# -----------------------------------------------------------

# endpoints
@app.route("/")
@login_required  # Add login protection to root route
def hello_world():
    return redirect(url_for('images.upload_image'))


# -----------------------------------------------------------
# Pipeline hooks
# -----------------------------------------------------------

from flask import jsonify

@app.errorhandler(UserAlreadyExistsError)
def handle_user_exists_error(error):
    return jsonify({'error': str(error)}), 400

@app.errorhandler(Exception)
def handle_exception(error):
    response, status_code = error_handler.handle_error(error)
    return jsonify(response), status_code

@app.before_request
def log_request_info():
    app.logger.info('Headers: %s', request.headers)
    app.logger.info('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    app.logger.info('Response Headers: %s', response.headers)
    return response
