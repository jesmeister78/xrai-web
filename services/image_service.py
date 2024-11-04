from pprint import pprint
from domain import db
from domain.entities import Image
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError

from domain.helpers import pretty_print

class ImageService:
    def __init__(self, db_session=None):
        """
        Initialize UserService with optional database session.
        
        Args:
            db_session: SQLAlchemy session to use. If None, uses default db.session
        """
        self.db = db_session or db.session

    def get_images(self): 
        try:
            images = db.session.execute(db.select(Image).order_by(Image.img_timestamp)).scalars()
        
            return images
        except Exception as e:
            print(str(e))

    
    

    def get_Images_for_procedure(self, proc_id: UUID) -> List[Image]:
        """
        Retrieve images for a specific proc from the database.
        
        Args:
            proc_id: The UUID of the proc
        Returns:
            List of Image objects
        """
        try:
            # Use scalar() for single result or all() for multiple results
            images = (
                db.session.query(Image)
                .filter(Image.procedure_id == proc_id)
                .order_by(Image.img_timestamp)
                .all()
            )
            print("Successfully retrieved Images from database")
            pprint(images)
            # pretty_print(images)
            return images

        except SQLAlchemyError as e:
            print(f"Database error occurred: {str(e)}")
            # You might want to log this error or handle it differently
            raise
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            raise
            
     
