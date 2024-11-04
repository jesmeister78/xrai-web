from flask import Flask, current_app
from typing import Optional

from domain import db
from services.image_service import ImageService
from services.procedure_service import ProcedureService
from services.user_service import UserService

class UserServiceExtension:
    def __init__(self, app: Optional[Flask] = None):
        self.user_service = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        self.user_service = UserService(db.session)

user_service_ext = UserServiceExtension(current_app)

class ProcedureServiceExtension:
    def __init__(self, app: Optional[Flask] = None):
        self.procedure_service = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        self.procedure_service = ProcedureService(db.session)

procedure_service_ext = ProcedureServiceExtension(current_app)


class ImageServiceExtension:
    def __init__(self, app: Optional[Flask] = None):
        self.image_service = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        self.image_service = ImageService(db.session)

image_service_ext = ImageServiceExtension(current_app)