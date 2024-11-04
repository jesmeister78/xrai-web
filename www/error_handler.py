from flask import jsonify
import traceback
from typing import Any, Dict, Tuple

class ErrorHandler:
    def __init__(self):
        self.handlers = {
            404: self._handle_404,
            500: self._handle_500,
            400: self._handle_400,
        }
        print("ErrorHandler registered")
    def handle_error(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """Main error handling method that routes to specific handlers"""
        if hasattr(error, 'code'):
            return self.handlers.get(error.code, self._handle_500)(error)
        return self._handle_500(error)

    def _handle_400(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        print("in 400 error handler", error)
        """Handle 400 Bad Request errors"""
        response = {
            'error': 'Bad Request',
            'message': str(error),
            'status_code': 400
        }
        return response, 400

    def _handle_404(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """Handle 404 Not Found errors"""
        response = {
            'error': 'Not Found',
            'message': str(error),
            'status_code': 404
        }
        return response, 404

    def _handle_500(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """Handle 500 Internal Server errors"""
        response = {
            'error': 'Internal Server Error',
            'message': str(error),
            'status_code': 500,
            'traceback': self._format_traceback(error)
        }
        return response, 500

    def _format_traceback(self, error: Exception) -> str:
        """Format traceback into a JSON-serializable string"""
        return ''.join(traceback.format_tb(error.__traceback__))

