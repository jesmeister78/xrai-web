# Reorganize imports in index.py
from flask import Flask, jsonify, redirect, request, url_for
from flask_login import LoginManager, login_required
import logging
import os
from datetime import datetime
import json

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

# Import routes
from www.routes import account, users, procedures, images
from www.template_filters import register_template_filters
from www.template_helpers import register_context_processors

# configure the web app

app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')
app.secret_key = 'whyneedthiskeyla'
app.config.from_pyfile(os.path.join(".", "config/app.conf"), silent=False)
app.logger.setLevel(logging.INFO)

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

# Register template filters
register_template_filters(app)

# Register context processors
register_context_processors(app)
    
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

def mask_sensitive_data(data):
    """Recursively process data structures and mask password fields."""
    if isinstance(data, dict):
        return {
            key: '*****' if key.lower() == 'password' 
            else mask_sensitive_data(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data

@app.before_request
def log_request_info():
    try:
        # Get basic request info
        request_info = {
            'url': request.url,
            'method': request.method,
            'headers': mask_sensitive_data(dict(request.headers))
        }

        # Handle different content types appropriately
        if request.content_type:
            if 'multipart/form-data' in request.content_type:
                files_info = {}
                for name, file in request.files.items():
                    files_info[name] = {
                        'filename': file.filename,
                        'content_type': file.content_type,
                        'content_length': request.headers.get('Content-Length')
                    }
                request_info['files'] = mask_sensitive_data(files_info)
            elif 'image/' in request.content_type:
                request_info['body'] = f"<Binary image data: {request.content_type}, length={request.content_length}>"
            elif request.is_json:
                request_info['body'] = mask_sensitive_data(request.get_json())
            elif 'application/x-www-form-urlencoded' in request.content_type:
                request_info['body'] = mask_sensitive_data(request.form.to_dict())
            else:
                request_info['body'] = f"<{request.content_type} data: length={request.content_length}>"

        app.logger.info('Request: %s', request_info)
    except Exception as e:
        app.logger.error(f"Error logging request: {str(e)}")

@app.after_request
def log_response_info(response):
    try:
        response_info = {
            'status_code': response.status_code,
            'headers': mask_sensitive_data(dict(response.headers))
        }

        # Handle different response types
        if response.direct_passthrough:
            response_info['body'] = f"<Binary data: {response.mimetype}, length={response.headers.get('Content-Length', 'unknown')}>"
        elif response.is_json:
            response_info['body'] = mask_sensitive_data(response.get_json())
        elif response.mimetype and 'image/' in response.mimetype:
            response_info['body'] = f"<Binary image data: {response.mimetype}, length={response.headers.get('Content-Length', 'unknown')}>"
        else:
            try:
                response_data = response.get_data(as_text=True)
                # Try to parse as JSON if possible, to mask sensitive data
                try:
                    import json
                    json_data = json.loads(response_data)
                    response_info['body'] = mask_sensitive_data(json_data)
                except:
                    response_info['body'] = response_data
            except:
                response_info['body'] = f"<{response.mimetype} data>"

        app.logger.info('Response: %s', response_info)
    except Exception as e:
        app.logger.error(f"Error logging response: {str(e)}")
    
    return response