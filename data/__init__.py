from flask_sqlalchemy import SQLAlchemy

from data.db import Base

db = SQLAlchemy(model_class=Base)
