from domain import db
from domain.entities import Image, Procedure
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError

class ProcedureService:
    def __init__(self, db_session=None):
        """
        Initialize UserService with optional database session.
        
        Args:
            db_session: SQLAlchemy session to use. If None, uses default db.session
        """
        self.db = db_session or db.session

    def get_procedures(self): 
        try:
            procedures = db.session.execute(db.select(Procedure).order_by(Procedure.case_number)).scalars()
        
            return procedures
        except Exception as e:
            print(str(e))

    
    

    def get_procedures_for_user(self, user_id: UUID) -> List[Procedure]:
        """
        Retrieve procedures for a specific user from the database.
        
        Args:
            user_id: The UUID of the user
        Returns:
            List of Procedure objects
        """
        try:
            # Use scalar() for single result or all() for multiple results
            procedures = (
                db.session.query(Procedure)
                .filter(Procedure.user_id == user_id)
                .all()
            )
            print("Successfully retrieved procedures from database")
            return procedures

        except SQLAlchemyError as e:
            print(f"Database error occurred: {str(e)}")
            # You might want to log this error or handle it differently
            raise
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            raise
            
        
    def get_proc_opt_images(self, id, inc_imgs):
        
        proc = (
            db.session.query(Procedure)
            .options(selectinload(Procedure.images).selectinload(Image.masks)).filter(Procedure.id == id).first() if inc_imgs 
            else db.session.query(Procedure).filter(Procedure.id == id).first()
        )
        # Assuming you have Procedure and Image models
        return proc
