from functools import wraps

from flask import copy_current_request_context, current_app
from flask_jwt_extended import verify_jwt_in_request
from werkzeug.exceptions import RequestTimeout
import threading
from typing import Callable, TypeVar, ParamSpec
import time

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



# class RequestTimeout(Exception):
#     pass

P = ParamSpec('P')
T = TypeVar('T')
def timeout(seconds: int) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            result = {'value': None, 'exception': None}
            
            # Capture the app instance from the current context
            app = current_app._get_current_object()
            
            # Wrap the function with the current request context
            @copy_current_request_context
            def target():
                # Create a new application context using the captured app instance
                with app.app_context():
                    try:
                        result['value'] = func(*args, **kwargs)
                    except Exception as e:
                        result['exception'] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)
            
            if thread.is_alive():
                thread.join(0)  # Clean up the thread
                raise RequestTimeout("Request timed out")
            
            if result['exception']:
                raise result['exception']
            
            if result['value'] is None:
                # Ensure we always return something valid
                return {'status': 'error', 'message': 'Operation completed but returned no value'}
                
            return result['value']
        return wrapper
    return decorator