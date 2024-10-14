from flask import Blueprint  

blueprint = Blueprint('users', __name__, url_prefix='/users')  

@blueprint.route('/') 
def list_users(): 
    # Logic for listing users 
    pass  

@blueprint.route('/<int:user_id>') 
def get_user(user_id): 
    # Logic for getting a specific user 
    pass