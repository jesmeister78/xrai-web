from datetime import datetime, timezone
import uuid
from data.entities import ClassMask, ClassMaskDetail, Image, Procedure, User
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow.fields import DateTime
from marshmallow import fields, post_load, pre_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow.utils import EXCLUDE
from dateutil import parser

class ClassMaskDetailSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ClassMaskDetail
        load_instance = True
        unknown = EXCLUDE
        
class ClassMaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ClassMask
        load_instance = True
        unknown = EXCLUDE

    code = fields.Str()
    name = fields.Str()
    colour = fields.Str()
    show = fields.Boolean()
    url = fields.Str()

class ImageSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Image
        # include_fk = True
        # load_instance = True
        unknown = EXCLUDE

    id = fields.UUID(missing=uuid.uuid4)
    procedure_id = fields.UUID(data_key='procedureId')
    img_timestamp = fields.DateTime(data_key='imageTimestamp')
    raw_img_src = fields.Str(data_key='rawImageSource')
    prediction_img_src = fields.Str(data_key='predictionImageSource')
    composite_img_src = fields.Str(data_key='compositeImageSource')
    labels_img_src = fields.Str(data_key='labelsImageSource')
    masks = fields.List(fields.Nested(ClassMaskSchema))

    @pre_load
    def process_input(self, data, **kwargs):
        data = data.copy()  # Create a mutable copy
        if 'imageTimestamp' not in data or not data['imageTimestamp']:
            data['imageTimestamp'] = datetime.now(timezone.utc).isoformat()
        elif isinstance(data['imageTimestamp'], str):
            try:
                # Try to parse the string as a datetime
                datetime.fromisoformat(data['imageTimestamp'].replace('Z', '+00:00'))
            except ValueError:
                # If parsing fails, use current time
                data['imageTimestamp'] = datetime.now(timezone.utc).isoformat()
        return data

    @post_load
    def make_image(self, data, **kwargs):
        image = Image(**data)
        return image

    
class ProcedureSchema(SQLAlchemyAutoSchema):
    date = DateTime(deserialize_from='date', deserialize=lambda value: parser.parse(value))
    class Meta:
        model = Procedure
        unknown = EXCLUDE
    id = fields.UUID()
    case_number = fields.Integer(data_key="caseNumber", dump_only=True)
    patient_name = fields.String(data_key="patientName")
    ur_identifier = fields.String(data_key="urIdentifier")
    date = fields.String()
    hospital = fields.String()
    surgeon = fields.String()
    surgery_type = fields.String(data_key="surgeryType")
    indication = fields.String()
    default_img_src = fields.String(data_key="defaultImageSource")
    user_id = fields.UUID()
    images = fields.Nested(ImageSchema, many=True)
    
    @post_load
    def make_procedure(self, data, **kwargs):
        image = Procedure(**data)
        return image
    
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        unknown = EXCLUDE
   