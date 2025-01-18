from flask import Blueprint, current_app, flash, render_template, session, request, redirect, url_for, jsonify
from datetime import timedelta
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user


from domain.exceptions import UserAlreadyExistsError
from domain.helpers import pretty_print
from domain.schemas import TokenSchema, UserSchema
from www.config.auth_config import jwt_blocklist
from services import user_service_ext

blueprint = Blueprint('account', __name__, url_prefix='/account')  
print("Account Blueprint registered")

# Inject services
user_service = user_service_ext.user_service


# -----------------------------------------------------------------------
# Web Routes
# -----------------------------------------------------------------------

@blueprint.route('/register', methods=['POST'])
def register():
    # Get user data
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    
    user = create_user(username, email, password)
    
    # Browser flow - create session and redirect
    session.permanent = True
    current_app.permanent_session_lifetime = timedelta(days=7)
    
    session['user_id'] = user.id
    session['username'] = user.username
    session['logged_in'] = True
    
    return redirect(url_for('images.upload_image'))

@blueprint.route('/login', methods=['GET'])
def login_form():
    if current_user.is_authenticated:
        return redirect(url_for('images.upload_image'))
    return render_template('account/login.html')
 
@blueprint.route('/register', methods=['GET'])
def register_form():
    return render_template('account/register.html')
    
@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if current_user.is_authenticated:
            return redirect(url_for('images.upload_image'))
    
        user = authenticate_user(request.form['username'], request.form['password'])

        if user is None:
            flash('Invalid username or password', 'error')
            return render_template('account/login.html', error=True)
            
        # Set "remember me" duration
        remember = request.form.get('remember', False)
        
        # This handles all session management
        login_user(user, remember=remember, duration=timedelta(days=7))
        
        flash('Logged in successfully!', 'success')
            
        # Redirect to the originally requested URL if it exists
        next_page = session.get('next')
        if next_page:
            session.pop('next', None)  # Remove the stored URL
            return redirect(next_page)
            
        return redirect(url_for('images.upload_image'))  # Default redirect
            
    return render_template('account/login.html')

@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('account.login'))


# -----------------------------------------------------------------------
# API Routes
# -----------------------------------------------------------------------
@blueprint.route('/', methods=['POST'])
def api_signup():
    try:
        # Get user data
        userid = request.json.get('id')
        username = request.json.get('username')
        password = request.json.get('password')
        email = request.json.get('email')
        print("about to create_user")
        
        user = create_user(userid, username, email, password)
        
        # Generate JWT for mobile clients
       
        return jsonify({
            'message': 'Signup successful',
            
        })
    except Exception as e:
        pretty_print(e)
        return jsonify(str(e)), 500
    
@blueprint.route('/token/', methods=['POST'])
def token():
    try:
        user = authenticate_user(request.json['username'], request.json['password'])
        user_data = UserSchema().dump(user)
        
        if user is None:
            return 'Login failed', 401
         
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        token_response = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            'token_type': 'Bearer',
            'expires_in': 30 * 24 * 3600
        }
        
        token_data = TokenSchema().dump(token_response)
        return jsonify({'user': user_data, 'token': token_data})
    except Exception as e:
        print(e)
        return jsonify(str(e)), 500


# Refresh token endpoint
@blueprint.route('/refresh/', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    refresh_token = create_refresh_token(identity=identity)
    
    return jsonify({"access_token": access_token, "refresh_token": refresh_token})
        
@blueprint.route("/token/", methods=["DELETE"])
@jwt_required()
def revoke():
    jti = get_jwt()["jti"]
    jwt_blocklist.add(jti)
    return jsonify({"msg": "Successfully logged out"})
# -----------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------   

def authenticate_user(username, password):
    user = user_service.verify_credentials(username, password)
    return user

def create_user(userid, username, email, password):

    if not userid or not username or not password or not email:
        return jsonify({'error': 'Missing required fields'}), 400
    print("in create_user2")
            
    # Check if user already exists
    
    if user_service.user_exists(username, email):
        raise UserAlreadyExistsError(f"User with username '{username}' or email '{email}' already exists")
    
    # Create new user
    hashed_password = generate_password_hash(password)
    user = user_service.create_user(userid, username, email, hashed_password)  # You'll need to implement this
    
    return user

