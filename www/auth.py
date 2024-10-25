from functools import wraps
from flask import current_app, jsonify, redirect, request, session, url_for
import jwt
import datetime

from www.config.auth_config import JWT_SECRET

# Function to generate JWT token
def generate_token(username):
    token = jwt.encode({
        'username': username,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token

# Helper function to verify JWT tokens
def verify_jwt():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
        
    token = auth_header.split(' ')[1]
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# Decorator for protected api routes
def mobile_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payload = verify_jwt()
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        return f(*args, **kwargs)
    return decorated

# Decorator for browser routes that require session auth
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
