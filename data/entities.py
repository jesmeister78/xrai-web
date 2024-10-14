from sqlalchemy import Boolean, Column, ForeignKey, UUID, ForeignKeyConstraint, Identity, Integer, PrimaryKeyConstraint, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from data import db

class User(db.Model):
    __tablename__ = "users"
    
    # Columns
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True)
    email = Column(String)
    
    # Relationships
    procedures = relationship("Procedure", back_populates="user")

    def __repr__(self):
        return f"User(id={self.id!r}, username={self.username!r})"

class Procedure(db.Model):
    __tablename__ = "procedures"
    
    def __init__(self, id, patient_name=None, ur_identifier=None, date=None,hospital=None, 
                 surgeon=None, surgery_type=None , indication=None, default_img_src=None, user_id=None):
        self.id = id
        self.patient_name = patient_name
        self.ur_identifier = ur_identifier
        self.date = date
        self.hospital = hospital
        self.surgeon = surgeon
        self.surgery_type = surgery_type
        self.indication = indication
        self.default_img_src = default_img_src
        self.user_id = user_id
    
    # Columns
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number = Column(Integer, Identity(start=1, increment=1), unique=True)
    patient_name = Column(String)
    ur_identifier = Column(String)
    date = Column(String)
    hospital = Column(String)
    surgeon = Column(String)
    surgery_type = Column(String)
    indication = Column(String)
    default_img_src = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Relationships
    user = relationship("User", back_populates="procedures")
    images = relationship("Image", back_populates="procedure")

    def __repr__(self):
        return f"Procedure(id={self.id!r}, case_number={self.case_number!r})"

class Image(db.Model):
    __tablename__ = "images"
    
    def __init__(self, id, img_timestamp, raw_img_src = None, prediction_img_src=None, composite_img_src=None, 
                 labels_img_src=None, procedure_id=None):
        self.id = id
        self.img_timestamp = img_timestamp
        self.raw_img_src = raw_img_src
        self.prediction_img_src = prediction_img_src
        self.composite_img_src = composite_img_src
        self.labels_img_src = labels_img_src
        self.procedure_id = procedure_id
        
    # Columns
    id = Column(UUID(as_uuid=True), primary_key=True)
    img_timestamp = Column(DateTime, default=datetime.now)
    raw_img_src = Column(String)
    prediction_img_src = Column(String)
    composite_img_src = Column(String)
    labels_img_src = Column(String)
    
    # Relationships
    procedure_id = Column(UUID(as_uuid=True), ForeignKey("procedures.id"))
    procedure = relationship("Procedure", back_populates="images")
    masks = relationship("ClassMask", back_populates="image")

    def __repr__(self):
        return f"Image(id={self.id!r})"

class ClassMask(db.Model):
    __tablename__ = "class_masks"
    
    # Columns
    code = Column(String, primary_key=True)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id"), primary_key=True)
    name = Column(String)
    colour = Column(String)
    show = Column(Boolean)
    url = Column(String)
    
    # Relationships
    image = relationship("Image", back_populates="masks")
    details = relationship("ClassMaskDetail", back_populates="class_mask")

    def __init__(
        self,
        code: str = None,
        name: str = None,
        colour: str = None,
        show: bool = None,
        url: str = None,
        image_id: UUID = None
    ):
        self.code = code
        self.name = name
        self.colour = colour
        self.show = show
        self.url = url
        self.image_id = image_id

    def __repr__(self) -> str:
        return f"ClassMask(code={self.code!r}, image_id={self.image_id!r}, name={self.name!r})"

class ClassMaskDetail(db.Model):
    __tablename__ = "class_mask_details"
    
    # Columns
    detail_code = Column(String, primary_key=True)
    class_mask_code = Column(String, primary_key=True)
    image_id = Column(UUID(as_uuid=True), primary_key=True)
    label = Column(String)
    value = Column(String)

    # Foreign Key Constraint
    __table_args__ = (
        ForeignKeyConstraint(
            ['class_mask_code', 'image_id'],
            ['class_masks.code', 'class_masks.image_id']
        ),
    )

    # Relationship
    class_mask = relationship("ClassMask", back_populates="details")
    
    def __repr__(self) -> str:
        return f"ClassMaskDetail(detail_code={self.detail_code!r}, class_mask_code={self.class_mask_code!r}, image_id={self.image_id!r})"