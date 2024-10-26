from flask import Blueprint, current_app, flash, render_template, session, request, redirect, url_for, jsonify
from datetime import timedelta, datetime
from werkzeug.security import generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user

import jwt

from www.config.auth_config import JWT_SECRET
from services import user_service_ext

blueprint = Blueprint('account', __name__, url_prefix='/account')  
print("Account Blueprint registered")

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
    

# @blueprint.route('/login', methods=['POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('images.upload_image'))
    
#     user = authenticate_user(request.form['username'], request.form['password'])

#     if user is None :
#         return 'Login failed', 401
        
#     if user:
#         # Set "remember me" duration
#         remember = request.form.get('remember', False)
        
#         # This handles all session management
#         login_user(user, remember=remember, duration=timedelta(days=7))
        
#         flash('Logged in successfully!', 'success')
        
#     return redirect(url_for('images.upload_image'))

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
    # Get user data
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    
    user = create_user(username, email, password)
    
    # Generate JWT for mobile clients
    token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(days=30)
    }, JWT_SECRET, algorithm='HS256')
    
    return jsonify({
        'message': 'Signup successful',
        'token': token,
        'token_type': 'Bearer',
        'expires_in': 30 * 24 * 3600
    })
    
@blueprint.route('/token', methods=['POST'])
def token():
    user = authenticate_user(request.json['username'], request.json['password'])
    if user is None :
        return 'Login failed', 401
    token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(days=30)
    }, JWT_SECRET, algorithm='HS256')
    
    return jsonify({
        'token': token,
        'token_type': 'Bearer',
        'expires_in': 30 * 24 * 3600
    })
        
    
# -----------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------   
# def user_exists(username, email):
#     return db.session.query(User).filter(
#         (User.username == username) | (User.email == email)
#     ).first() is not None

def authenticate_user(username, password):
    user_service = user_service_ext.user_service
    user = user_service.verify_credentials(username, password)
    return user

def create_user(username, email, password):
    if not username or not password or not email:
        return jsonify({'error': 'Missing required fields'}), 400
            
    # Check if user already exists
    user_service = user_service_ext.user_service
    
    if user_service.user_exists(username, email):
        return jsonify({'error': 'User already exists'}), 400
    
    # Create new user
    hashed_password = generate_password_hash(password)
    user = user_service.create_user(username, email, hashed_password)  # You'll need to implement this
    
    return user

# def verify_credentials(username, password):
#     user = db.session.query(User).filter_by(username=username).first()
#     if user and check_password_hash(user.password, password):
#         return user
#     return None