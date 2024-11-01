from flask_sqlalchemy import SQLAlchemy

from domain.db import Base

db = SQLAlchemy(model_class=Base)
