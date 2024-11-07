from functools import wraps

from flask import current_app
from flask_jwt_extended import verify_jwt_in_request


def debug_jwt(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"JWT Verification Failed: {str(e)}")
            return {"msg": f"Detailed error: {str(e)}"}, 422
    return wrapper