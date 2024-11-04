import traceback
from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import jwt_required

from domain import db
from domain.helpers import patch_from_json, pretty_print, print_dict
from domain.schemas import ImageSchema, ProcedureSchema
from domain.entities import Image, Procedure
from services import procedure_service_ext, image_service_ext

blueprint = Blueprint('procedures', __name__, url_prefix='/procedures')  
print("Procedures Blueprint registered")

# Inject services
procedure_service = procedure_service_ext.procedure_service
image_service = image_service_ext.image_service

# -----------------------------------------------------------------------
# WEB Routes
# -----------------------------------------------------------------------

@blueprint.route('/list', methods=["GET"]) 
def list_procedures(): 
    procedures = db.session.execute(db.select(Procedure).order_by(Procedure.case_number)).scalars()
    return render_template("procedure/list.html", procedures=procedures)

# -----------------------------------------------------------------------
# API Routes
# -----------------------------------------------------------------------

@blueprint.route('/', methods=["GET"]) 
@jwt_required()
def get_procedures(): 
    try:
        procedures = db.session.execute(db.select(Procedure).order_by(Procedure.case_number)).scalars()
       
        vm = ProcedureSchema().dump(procedures, many=True) 
        return jsonify(vm)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'stack_trace': e.__traceback__
            
            })
        
@blueprint.route('/<uuid:procedure_id>/', methods=["GET"]) 
@jwt_required()
def get_procedure(procedure_id): 
    inc_imgs = request.args.get("inc_imgs", False)
    proc = procedure_service.get_proc_opt_images(procedure_id, inc_imgs)
    vm = ProcedureSchema().dump(proc)
    
    print(f"vm: {vm}")
    
    return jsonify(vm), 200

@blueprint.route('/<uuid:procedure_id>/images/', methods=["GET"]) 
@jwt_required()
def get_procedure_images(procedure_id):
    try:

        images = image_service.get_Images_for_procedure(procedure_id)
        vm = ImageSchema().dump(images, many=True)
        
        print(f"vm:")
        pretty_print(vm)
        
        return jsonify(vm), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'stack_trace': e.__traceback__
            
            })
        
@blueprint.route('/<uuid:id>/', methods=["PATCH"]) 
@jwt_required()
def update_procedure(id): 
    try:
        proc = db.session.get(Procedure, id)
        payload = request.json
        patch_from_json(payload, proc, {"image": "img", "source": "src"}) 
        db.session.commit() 
        vm = ProcedureSchema().dump(proc)
        return jsonify(vm)

    except Exception as e:
        print(e)
        return jsonify({
            'error': "An unexpected error occurred",
            'details': str(e),
            'stack_trace': traceback.format_exc()
        }), 500  # Internal Server Error

@blueprint.route('/', methods=["POST"]) 
@jwt_required()
def add_procedure():
    try:
        print_dict(request.json)
        proc: Procedure = ProcedureSchema().load(request.json, session=db.session)
    
        db.session.add(proc)
        db.session.commit()
        vm = ProcedureSchema().dump(proc)
        return jsonify(vm)
    except Exception as e:
        print(e)
        return jsonify({
            'error': "An unexpected error occurred",
            'details': str(e),
            'stack_trace': traceback.format_exc()
        }), 500  # Internal Server Error
   
        
  
# -----------------------------------------------------------
# Functions
# -----------------------------------------------------------
