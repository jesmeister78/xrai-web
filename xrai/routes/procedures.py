import traceback
from flask import Blueprint, jsonify, render_template, request

from data import db
from data.helpers import patch_from_json, print_dict
from data.schemas import ImageSchema, ProcedureSchema
from data.entities import Image, Procedure
from sqlalchemy.orm import selectinload

blueprint = Blueprint('procedures', __name__, url_prefix='/procedures')  


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
        
@blueprint.route('/<uuid:procedure_id>', methods=["GET"]) 
def get_procedure(procedure_id): 
    inc_imgs = request.args.get("inc_imgs", False)
    proc = get_proc_opt_images(procedure_id, inc_imgs)
    vm = ProcedureSchema().dump(proc)
    
    print(f"vm: {vm}")
    
    return jsonify(vm), 200

@blueprint.route('/<uuid:procedure_id>/images', methods=["GET"]) 
def get_procedure_images(procedure_id):

    # Assuming you have Procedure and Image models
    proc = get_proc_opt_images(procedure_id, True)
    # Now you can access the images without additional queries
    # for image in result.images:
    #     print(image.id)
    vm = ImageSchema().dump(proc.images, many=True)
    
    print(f"vm: {vm}")
    
    return jsonify(vm), 200
        
@blueprint.route('/<uuid:id>', methods=["PATCH"]) 
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

def get_proc_opt_images(id, inc_imgs):
    
    proc = (
        db.session.query(Procedure)
        .options(selectinload(Procedure.images).selectinload(Image.masks)).filter(Procedure.id == id).first() if inc_imgs 
        else db.session.query(Procedure).filter(Procedure.id == id).first()
            )
    # Assuming you have Procedure and Image models
    return proc