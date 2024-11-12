from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from domain.schemas import ImageSchema, ProcedureSchema
from services import procedure_service_ext, image_service_ext
import traceback

blueprint = Blueprint('procedures', __name__, url_prefix='/procedures')
print("Procedures Blueprint registered")

# Inject services
procedure_service = procedure_service_ext.procedure_service
image_service = image_service_ext.image_service

# WEB Routes
@blueprint.route('/list', methods=["GET"])
def list_procedures():
    try:
        procedures = procedure_service.get_all_procedures()
        return render_template("procedure/list.html", procedures=procedures)
    except Exception as e:
        # You might want to handle this error differently for web routes
        return render_template("error.html", error=str(e))

# API Routes
@blueprint.route('/', methods=["GET"])
@jwt_required()
def get_procedures():
    try:
        procedures = procedure_service.get_all_procedures()
        return jsonify(ProcedureSchema().dump(procedures, many=True))
    except Exception as e:
        return jsonify({
            'error': str(e),
            'stack_trace': traceback.format_exc()
        }), 500

@blueprint.route('/<uuid:procedure_id>/', methods=["GET"])
@jwt_required()
def get_procedure(procedure_id):
    try:
        include_images = request.args.get("inc_imgs", False)
        procedure = procedure_service.get_procedure_by_id(procedure_id, include_images)
        
        if not procedure:
            return jsonify({'error': 'Procedure not found'}), 404
            
        return jsonify(ProcedureSchema().dump(procedure)), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'stack_trace': traceback.format_exc()
        }), 500

@blueprint.route('/<uuid:procedure_id>/images/', methods=["GET"])
@jwt_required()
def get_procedure_images(procedure_id):
    try:
        images = image_service.get_Images_for_procedure(procedure_id)
        return jsonify(ImageSchema().dump(images, many=True)), 200
    except Exception as e:
        return jsonify({
            'error': str(e),
            'stack_trace': traceback.format_exc()
        }), 500

@blueprint.route('/<uuid:id>/', methods=["PATCH"])
@jwt_required()
def update_procedure(id):
    try:
        procedure = procedure_service.update_procedure(id, request.json)
        return jsonify(ProcedureSchema().dump(procedure))
    except ValueError as e:
        return jsonify({
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'error': "An unexpected error occurred",
            'details': str(e),
            'stack_trace': traceback.format_exc()
        }), 500

@blueprint.route('/', methods=["POST"])
@jwt_required()
def add_procedure():
    try:
        procedure = procedure_service.create_procedure(request.json)
        return jsonify(ProcedureSchema().dump(procedure))
    except Exception as e:
        return jsonify({
            'error': "An unexpected error occurred",
            'details': str(e),
            'stack_trace': traceback.format_exc()
        }), 500