from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from domain.schemas import ProcedureSchema
from services import procedure_service_ext

blueprint = Blueprint('users', __name__, url_prefix='/users')  
print("Users Blueprint registered")

# Inject services

procedure_service = procedure_service_ext.procedure_service


@blueprint.route('/') 
def list_users(): 
    # Logic for listing users 
    pass  

@blueprint.route('/<int:user_id>/') 
def get_user(user_id): 
    # Logic for getting a specific user 
    pass


@blueprint.route('/<uuid:user_id>/procedures/', methods=['GET'])
@jwt_required()
def get_procs_for_user(user_id):
    try:
        print("about to call procs returned from service")
        procs = procedure_service.get_procedures_for_user(user_id)
    # Now you can access the images without additional queries
    # for image in result.images:
    #     print(image.id)
        print("procs returned from service")
        vm = ProcedureSchema().dump(procs, many=True)
        
        print(f"vm: {vm}")
        
        return jsonify(vm), 200
    except Exception as e:
        print(e)
        return jsonify(str(e)), 500
    
    
    