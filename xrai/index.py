import os
import logging
from flask import Flask


from data import db

# import routes
from xrai.routes import users, procedures, images
# configure the web app

app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')
app.secret_key = 'whyneedthiskeyla'
app.config.from_pyfile(os.path.join(".", "config/app.conf"), silent=False)
app.logger.setLevel(logging.INFO)

# Register routes from other files 
app.register_blueprint(users.blueprint) 
app.register_blueprint(procedures.blueprint)
app.register_blueprint(images.blueprint)

# -----------------------------------------------------------

# configure the database

# Configure the SQLAlchemy connection URI 
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://xraidbAdmin:Password01@localhost:5432/xraidb' 
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# initialize the app with the extension
db.init_app(app)
# create the tables (tables are not updated if they already exist in db. we will remove this statement once schema is stable)
with app.app_context():
    db.create_all()
# -----------------------------------------------------------

# endpoints

@app.route("/")
def hello_world():
    return "Hello, World!"
