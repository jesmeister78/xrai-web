from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from typing import Optional

from data import db
from data.entities import User


class UserService:
    def __init__(self, db_session=None):
        """
        Initialize UserService with optional database session.
        
        Args:
            db_session: SQLAlchemy session to use. If None, uses default db.session
        """
        self.db = db_session or db.session

    def user_exists(self, username: str, email: str) -> bool:
        """
        Check if a user exists with the given username or email.
        
        Args:
            username: Username to check
            email: Email to check
            
        Returns:
            bool: True if user exists, False otherwise
        """
        return self.db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first() is not None

    def create_user(self, username: str, email: str, hashed_password: str) -> User:
        """
        Create a new user with the given credentials.
        
        Args:
            username: Username for the new user
            email: Email for the new user
            hashed_password: Pre-hashed password for the new user
            
        Returns:
            User: Newly created user object
            
        Raises:
            SQLAlchemyError: If there's a database error
        """
        user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        self.db.add(user)
        self.db.commit()
        return user

    def verify_credentials(self, username: str, password: str) -> Optional[User]:
        """
        Verify user credentials and return the user if valid.
        
        Args:
            username: Username to verify
            password: Plain text password to verify
            
        Returns:
            Optional[User]: User object if credentials are valid, None otherwise
        """
        user = self.db.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            return user
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by their ID.
        
        Args:
            user_id: ID of the user to retrieve
            
        Returns:
            Optional[User]: User object if found, None otherwise
        """
        return self.db.query(User).get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by their username.
        
        Args:
            username: Username of the user to retrieve
            
        Returns:
            Optional[User]: User object if found, None otherwise
        """
        return self.db.query(User).filter_by(username=username).first()