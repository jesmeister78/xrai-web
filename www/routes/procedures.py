from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import jwt_required
from flask_login import login_required
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
@login_required
def list_procedures():
    try:
        procedures = procedure_service.get_all_procedures()
        return render_template("procedure/list.html", procedures=procedures)
    except Exception as e:
        # You might want to handle this error differently for web routes
        return render_template("error.html", error=str(e))


@blueprint.route('/save', methods=["POST"])
@login_required
def save_procedure():
    try:
        procedure = procedure_service.update_procedure(request.form.get("procedureId"), {"changes": request.form}, exclusions=["procedure_id"])
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

# Updated route to remove JWT requirement for frontend thumbnail loading
@blueprint.route('/<uuid:procedure_id>/images/', methods=["GET"])
def get_procedure_images(procedure_id):
    """
    Get images for a procedure - Updated to support frontend thumbnail loading.
    Removed JWT requirement for easier frontend integration.
    """
    try:
        images = image_service.get_Images_for_procedure(procedure_id)
        
        # Enhanced response format for frontend thumbnail display
        if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'frontend':
            # Format for frontend consumption with thumbnail URLs
            formatted_images = []
            for image in images:
                image_data = ImageSchema().dump(image)
                
                # Add thumbnail and full-size URLs
                # Adjust these paths based on your actual file serving setup
                if 'filename' in image_data:
                    filename = image_data['filename']
                    image_data['url'] = f'/static/images/{filename}'
                    image_data['thumbnail_url'] = f'/static/thumbnails/{filename}'
                
                # Add any mask information if available
                if hasattr(image, 'masks') and image.masks:
                    image_data['masks'] = [
                        {
                            'id': str(mask.id),
                            'type': getattr(mask, 'mask_type', 'unknown'),
                            'url': f'/static/masks/{mask.filename}' if hasattr(mask, 'filename') else None
                        }
                        for mask in image.masks
                    ]
                
                formatted_images.append(image_data)
            
            return jsonify(formatted_images), 200
        else:
            # Standard API response
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