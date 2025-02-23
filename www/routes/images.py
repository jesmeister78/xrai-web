import os
from flask import Blueprint, flash, jsonify, redirect, render_template, request, send_from_directory, url_for, current_app
from flask_jwt_extended import jwt_required
from flask_login import login_required
from sqlalchemy.orm.exc import NoResultFound
import traceback

from domain.constants import ATTR_MAP
from services import image_service_ext
from domain.schemas import ImageSchema
from www.utils import debug_jwt, timeout

# Register Blueprint
blueprint = Blueprint('images', __name__, url_prefix='/images')
print("Images Blueprint registered")

# Inject Services
image_service = image_service_ext.image_service



# -----------------------------------------------------------------------
# WEB Routes
# -----------------------------------------------------------------------

@blueprint.route('/<int:image_id>')
def get_image(image_id):
    pass

@blueprint.route('/process_and_view', methods=['POST'])
def process_and_view():
    name = request.args.get('name')
    caseNum = request.args.get('caseNum')
    image_service.process_image(name, caseNum, False)
    return redirect(url_for('images.show_processed_images', img_id=name))

@blueprint.route('/clear_processed', methods=['GET', 'POST'])
def clear_processed():
    image_service.clear_processed_images()
    return redirect(url_for('images.upload_image'))

@blueprint.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_image():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and image_service.allowed_file(file.filename):
            image = image_service.save_uploaded_file(file, request.form)
            return render_template('image/show.html', path=file.filename)
        
    return render_template('image/upload.html')

@blueprint.route('/show_image/<path:path>', methods=['GET'])
def show_image(path):
    return send_from_directory('static/images', path)

@blueprint.route('/process/<string:img_id>', methods=['GET', 'POST'])
def show_processed_images(img_id: str):
    path = os.path.join(current_app.config['STATIC_FOLDER'], 
                       current_app.config['TEMP_OUTPUT_FOLDER'])
    images = image_service.get_related_images(path, img_id)
    #debug
    print("Images:")
    print(images)
    return render_template('image/processed.html', 
                         images=images,
                         attr_map=ATTR_MAP)

@blueprint.route('/samples', methods=['GET'])
def show_samples():
    path = os.path.join(current_app.config['STATIC_FOLDER'], 
                       current_app.config['SAMPLE_IMAGES_FOLDER'])
    images = image_service.get_images_from_path(path)
    return render_template('image/samples.html', images=images)


# -----------------------------------------------------------------------
# API Routes
# -----------------------------------------------------------------------

@blueprint.route('/', methods=['POST'])
@jwt_required()
@debug_jwt
def api_add():
    try:
        if 'image' not in request.files:
            raise FileNotFoundError("No file in request")
        
        file = request.files['image']
        if file.filename == '':
            raise NameError("Filename cannot be blank")
        
        if not image_service.allowed_file(file.filename):
            raise NameError(f"Filename '{file.filename}' is not allowed")
            
        image = image_service.save_uploaded_file(file, request.form)
        return jsonify(ImageSchema().dump(image))
        
    except (FileNotFoundError, NameError) as e:
        return jsonify({
            'error': str(e),
            'stack_trace': traceback.format_exc()
        }), 400
    except Exception as e:
        return jsonify({
            'error': "An unexpected error occurred",
            'details': str(e),
            'stack_trace': traceback.format_exc()
        }), 500

@blueprint.route('/<uuid:id>/', methods=['PUT'])
@jwt_required()
@timeout(300)
def api_update(id):
    try:
        image = image_service.process_and_update_image(id)
        return jsonify(ImageSchema().dump(image)), 200
    except NoResultFound as e:
        return jsonify({
            'error': "Not Found",
            'details': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'error': "Image processing failed.",
            'details': str(e)
        }), 500

@blueprint.route('/<uuid:id>/', methods=['DELETE'])
@jwt_required()
def api_delete(id):
    # first try to delete the image from the database (with cascade on delete)
    # then if  successful, we will delete the image file from the web server
    try:
        if(image_service.delete_image_by_id(id)):
            image_service.delete_image_file(str(id), False)
            
        return jsonify({"message": "image deleted"}), 200
    except Exception as e:
        return jsonify({
            'error': "An unexpected error occurred",
            'details': str(e),
            'stack_trace': traceback.format_exc()
        }), 500
    

@blueprint.route('/<uuid:id>/', methods=['PATCH'])
@jwt_required()
def api_patch(id):
    try:
        image = image_service.patch_image(id, request.json)
        return jsonify(ImageSchema().dump(image))
    except Exception as e:
        return jsonify({
            'error': "An unexpected error occurred",
            'details': str(e),
            'stack_trace': traceback.format_exc()
        }), 500