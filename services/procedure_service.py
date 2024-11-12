from domain import db
from domain.entities import Image, Procedure
from domain.helpers import patch_from_json
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.exc import SQLAlchemyError
from domain.schemas import ProcedureSchema

class ProcedureService:
    def __init__(self, db_session=None):
        """Initialize ProcedureService with optional database session."""
        self.db = db_session or db.session

    def get_all_procedures(self) -> List[Procedure]:
        """Get all procedures ordered by case number."""
        try:
            return (self.db.execute(db.select(Procedure)
                   .order_by(Procedure.case_number))
                   .scalars())
        except SQLAlchemyError as e:
            print(f"Database error occurred: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            raise

    def get_procedures_for_user(self, user_id: UUID) -> List[Procedure]:
        """
        Retrieve procedures for a specific user.
        
        Args:
            user_id: The UUID of the user
        Returns:
            List of Procedure objects
        """
        try:
            procedures = (
                self.db.query(Procedure)
                .filter(Procedure.user_id == user_id)
                .all()
            )
            print("Successfully retrieved procedures from database")
            return procedures
        except SQLAlchemyError as e:
            print(f"Database error occurred: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            raise

    def get_procedure_by_id(self, procedure_id: UUID, include_images: bool = False) -> Optional[Procedure]:
        """
        Get a procedure by ID with optional image loading.
        
        Args:
            procedure_id: The UUID of the procedure
            include_images: Whether to load associated images and masks
        Returns:
            Procedure object or None if not found
        """
        try:
            query = self.db.query(Procedure)
            
            if include_images:
                query = query.options(
                    selectinload(Procedure.images).selectinload(Image.masks)
                )
                
            return query.filter(Procedure.id == procedure_id).first()
            
        except SQLAlchemyError as e:
            print(f"Database error occurred: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            raise

    def create_procedure(self, procedure_data: Dict) -> Procedure:
        """
        Create a new procedure from the provided data.
        
        Args:
            procedure_data: Dictionary containing procedure data
        Returns:
            Created Procedure object
        """
        try:
            procedure: Procedure = ProcedureSchema().load(procedure_data, session=self.db)
            self.db.add(procedure)
            self.db.commit()
            return procedure
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error occurred: {str(e)}")
            raise
        except Exception as e:
            self.db.rollback()
            print(f"Unexpected error occurred: {str(e)}")
            raise

    def update_procedure(self, procedure_id: UUID, update_data: Dict) -> Procedure:
        """
        Update an existing procedure with the provided data.
        
        Args:
            procedure_id: The UUID of the procedure to update
            update_data: Dictionary containing fields to update
        Returns:
            Updated Procedure object
        """
        try:
            procedure = self.db.get(Procedure, procedure_id)
            if not procedure:
                raise ValueError(f"Procedure with id {procedure_id} not found")
                
            patch_from_json(update_data, procedure, {"image": "img", "source": "src"})
            self.db.commit()
            return procedure
            
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"Database error occurred: {str(e)}")
            raise
        except Exception as e:
            self.db.rollback()
            print(f"Unexpected error occurred: {str(e)}")
            raise