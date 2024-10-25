import os
import logging
from flask import Flask, jsonify, request
from flask_login import LoginManager

# local imports
from data import db
from www import error_handler
from www.routes import account, users, procedures, images
from services import user_service_ext

# configure the web app

app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')
app.secret_key = 'whyneedthiskeyla'
app.config.from_pyfile(os.path.join(".", "config/app.conf"), silent=False)
app.logger.setLevel(logging.INFO)

# init the login manager

login_manager = LoginManager()

login_manager.init_app(app)
login_manager.login_view = 'account.login'
    
# User loader function
@login_manager.user_loader
def load_user(user_id):
    user_service = user_service_ext.user_service
    return user_service.get_user_by_id(user_id)

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
def hello_world():
    return "Hello, World!"


# -----------------------------------------------------------
# Pipeline hooks
# -----------------------------------------------------------


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
