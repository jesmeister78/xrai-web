from flask import Flask, current_app
from typing import Optional

from domain import db
from services.user_service import UserService

class UserServiceExtension:
    def __init__(self, app: Optional[Flask] = None):
        self.user_service = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        self.user_service = UserService(db.session)

user_service_ext = UserServiceExtension(current_app)