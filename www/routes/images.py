from datetime import datetime
import os
import pprint
import shutil
import traceback
from flask import Blueprint, flash, jsonify, redirect, render_template, request, send_from_directory, url_for, current_app  
from flask_login import login_required
from marshmallow import ValidationError
from werkzeug.utils import secure_filename
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
from PIL import Image as PILImage

# local imports
from domain import db
from domain.helpers import patch_from_json, pretty_print, print_dict, update_from_camel
from domain.schemas import ImageSchema
from domain.entities import ClassMask, Image
from www.constants import ATTR_MAP, ATTR_NAME_MAP
from xrai_engine.image_processor import ImageProcessor


blueprint = Blueprint('images', __name__, url_prefix='/images')  

print("Images Blueprint registered")


# -----------------------------------------------------------------------
# WEB Routes
# -----------------------------------------------------------------------

@blueprint.route('/<int:image_id>') 
def get_image(image_id): 
    # Logic for getting a specific image 
    pass

@blueprint.route('/process_and_view', methods=['POST'])
def process_and_view():
    name = request.args.get('name')
    caseNum = request.args.get('caseNum')
    process_image(name, caseNum, False)
    return redirect(url_for('images.show_processed_images'))

@blueprint.route('/clear_processed', methods=['GET', 'POST'])
def clear_processed():
    
    # delete the original uploaded image from the staging folder
    folder = os.path.join(current_app.root_path, 'static', 'images', 'processed')

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            # elif os.path.isdir(file_path):
            #     shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    return redirect(url_for('images.upload_image'))

@blueprint.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_image():
    
    if request.method == 'POST':
        
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # save the image file to the file system
            file.save(os.path.join(current_app.root_path, 'static', 'images', filename))
            
            # add a new image record to the database
            image: Image = ImageSchema().load(request.form)   # dict_to_entity(image_schema, request.form)
            
            # save the new image object to the database
            db.session.add(image)
            db.session.commit()
       
            return render_template('image/show.html', path=filename)
        
    return render_template('image/upload.html')
   
@blueprint.route('/show_image/<path:path>', methods=['GET'])
def show_image(path):

    return send_from_directory('static/images', path)

@blueprint.route('/processed', methods=['GET','POST'])
def show_processed_images():
    # ALLOWED_EXTENSIONS = {'.png', '.jpeg', '.jpg'}
    
    # # Print the full path being accessed
    # full_path = os.path.join(current_app.root_path, current_app.config['STATIC_FOLDER'], current_app.config['TEMP_OUTPUT_FOLDER'])
    # print("Accessing directory:", full_path)
    
    # # Get and print all files in directory
    # files = os.listdir(full_path)
    # print("All files found:", files)
    
    # # Filter and print matched files
    # images = [file for file in files if os.path.splitext(file)[1].lower() in ALLOWED_EXTENSIONS]
    # print("Filtered images:", images)
    
    # # Create and print final paths
    # images = ['images/processed/' + file for file in images]
    # print("Final image paths:", images)
    path = os.path.join(current_app.config['STATIC_FOLDER'], current_app.config['TEMP_OUTPUT_FOLDER'])
    images = get_images(path)
    return render_template('image/processed.html', 
                         images=images,
                         attr_map=ATTR_MAP)  # Pass the map to the template

@blueprint.route('/samples', methods=['GET'])
def show_samples():
   
    path = os.path.join(current_app.config['STATIC_FOLDER'], current_app.config['SAMPLE_IMAGES_FOLDER'])
    images = get_images(path)
    return render_template('image/samples.html', images=images)  
# -----------------------------------------------------------------------
# API Routes
# -----------------------------------------------------------------------


@blueprint.route('/', methods=['POST'])
def api_add():
    
    try:    
        # check if the post request has the file part
        if 'image' not in request.files:
            raise FileNotFoundError("No file in request")
        
        file = request.files['image']
        
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            raise NameError("Filename cannot be blank")
        
        if not allowed_file(file.filename):
            raise NameError(f"Filename '{file.filename}' is not allowed")
        else:
            filename = secure_filename(file.filename)
            
            # save the image file to the file system
            path = os.path.join('static', 'images', filename)
            file.save(os.path.join(current_app.root_path, path))
            
            # add a new image record to the database
            image: Image = ImageSchema().load(request.form, session=db.session)   # dict_to_entity(image_schema, request.form)
            
            # update the new file path
            image.raw_img_src = f"/images/{filename}"
            
            # save the new image object to the database
            db.session.add(image)
            db.session.commit()
        
            # return the serialised view model
            vm = ImageSchema().dump(image)
        
            return jsonify(vm)
        
    except FileNotFoundError as e:
        print(e)
        return jsonify({
            'error': str(e),
            'stack_trace': traceback.format_exc()
        }), 400  # Bad Request

    except NameError as e:
        print(e)
        return jsonify({
            'error': str(e),
            'stack_trace': traceback.format_exc()
        }), 400  # Bad Request

    except Exception as e:
        print(e)
        return jsonify({
            'error': "An unexpected error occurred",
            'details': str(e),
            'stack_trace': traceback.format_exc()
        }), 500  # Internal Server Error
       
@blueprint.route('/<string:id>', methods=['PUT'])
def api_update(id):
    processed_image = process_and_update_image(id)
    # print(f"processed_image: {processed_image}")
    # pretty_print(processed_image)
    vm = ImageSchema().dump(processed_image)
    
    # print(f"vm: {vm}")
    
    return jsonify(vm), 200
    
    
@blueprint.route('/<string:id>', methods=['PATCH'])
def api_patch(id):

    try:    
        
        # get the raw image by id
        image = db.session.get(Image, id)  
        print(f"image: {image}")
        print_dict(request.json)
        # patch from the changes in the json
        patch_from_json(request.json, image)
        
        # save the updated image object to the database
        db.session.commit()
    
        # return the serialised view model
        vm = ImageSchema().dump(image)
        
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

def get_images(path):
    ALLOWED_EXTENSIONS = {'.png', '.jpeg', '.jpg'}
    
    # Print the full path being accessed
    full_path = os.path.join(current_app.root_path, path)
    print("Accessing directory:", full_path)
    
    # Get and print all files in directory
    files = os.listdir(full_path)
    print("All files found:", files)
    
    # Filter and print matched files
    images = [file for file in files if os.path.splitext(file)[1].lower() in ALLOWED_EXTENSIONS]
    print("Filtered images:", images)
    
    # Create and print final paths
    images = [os.path.join(path, file).replace('static/', '') for file in images]
    print("Final image paths:", images)
    
    return images
   

def process_and_update_image(image_id):
    try:
        # Step 1: Get existing Image from the database
        image = db.session.query(Image).filter(Image.id == image_id).one()
        
        # Step 2: Call external lib to process image
        processed_image_data = process_image(image.id, image.procedure_id, True)
        # hack to fix "labels_img_src" until we implement it
        processed_image_data["labels_img_src"] = "" 
        # Combined Step 3 & 4: Update existing image with new data using schema.load()
        try:
            print_dict(processed_image_data)
            # We have moved the original image so update the rawImageSource
            # processed_image_data["rawImageSource"] = processed_image_data["rawImageSource"].replace('_raw.png', '.jpeg')
            # TODO we should be using marshmallow schemas here
            update_from_camel(processed_image_data, image, replacements={"image": "img", "source": "src"}, exclusions=["masks"])
           
            # load the masks into entities and save them
            # TODO we should be using marshmallow schemas here
            with db.session.no_autoflush:
                for mask in processed_image_data["masks"]:
                    mask_entity: ClassMask = update_from_camel(mask, ClassMask(), exclusions=["details"])
                    mask_entity.image_id = image.id
                    db.session.add(mask_entity)
                    image.masks.append(mask_entity)
                
        except ValidationError as validation_error:
            pprint(validation_error.messages)
            # Handle validation errors
            db.session.rollback()
            return jsonify({
                'error': "Validation error",
                'details': validation_error.messages
            }), 400
        
        # Step 5: Save the modified Image back to the database
        try:
            print("about to db commit")
            db.session.commit()
            print("db commit success")
        except SQLAlchemyError as db_error:
            # Handle database errors
            db.session.rollback()
            print(f"db rollback success: {db_error}")
            return jsonify({
                'error': "Database error",
                'details': str(db_error)
            }), 500
        except Exception as e:
            return jsonify({
                'error': str(e),
                'stack_trace': e.__traceback__
                
                })
        print(f"Returning image: {image}")
        return image
    
    except NoResultFound:
        return jsonify({
            'error': "Not Found",
            'details': f"No Image found with id {image_id}"
        }), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': "An unexpected error occurred",
            'details': str(e)
        }), 500
  
def process_image(name, proc_id, do_rotation=True):
    try:
        # image_data = request.files['image']  # Access the uploaded image
        # for now we are just sending a file from hardcoded filesystem path
        # xrai_engine will always pull the raw image from config['APP_ROOT_FOLDER']/xrai/static/images
        # Process the image (e.g., save to disk, analyze, etc.)
        experiment_folder = os.path.join(current_app.config['APP_ROOT_FOLDER'], current_app.config['EXPERIMENT_FOLDER'])
        experiment_name = current_app.config['EXPERIMENT_NAME']
        config_folder = os.path.join(current_app.config['APP_ROOT_FOLDER'], current_app.config['CONFIG_FOLDER'])
        
        imageProcessor = ImageProcessor(experiment_name, experiment_folder, config_folder, 0)
        
        print(f"do_rotation: {do_rotation}")

        raw_mask_comp = imageProcessor.processImage(0, False, do_rotation)
        current_app.logger.info('process_image: xrai_engine completed successfully')
        
        # this will map to a ProcessedImage in the javascript app
        # and save the images returned by xrai-engine to local filesystem
        processed_image = {
            "id": name,
            "procedureId": proc_id,
            "imageTimestamp":  datetime.now()
        }  | save_image_files(raw_mask_comp, do_rotation)    
        
        print("save images completed")
        
        # delete the original uploaded image from the staging folder
        folder = os.path.join(current_app.root_path, 'static', 'images')

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                # delete the file
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
        return processed_image
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'stack_trace': e.__traceback__
            
            })
       
def save_image_files(img_arr, do_rotation):
        
    #img_types = ['raw', 'mask', 'composite', 'label_mask', 'label_composite']
    img_paths = {}
    img_paths['masks'] = []
    
    for idx, i in enumerate(img_arr):
        filename = secure_filename(i['name'])
        img_file = i['img']
        img_url = url_for("static", filename=f"{current_app.config['TEMP_OUTPUT_FOLDER']}/{filename}")
        #current_app.logger.info('save_images: processing img_arr: img_url: %s', img_url)
        img_paths = process_image_path(img_paths, filename)
        # save the images returned by xrai-engine to local filesystem
        save_path = os.path.join(current_app.root_path, 'static', 'images', 'processed', filename)
        # current_app.logger.info('save_images: processing img_arr: save_path: %s', save_path)
        img_file.save(save_path)
        if os.path.isfile(save_path):
            current_app.logger.info(f'save_images: img {i["name"]} saved successfully')
        else:
            current_app.logger.info(f'save_images: img {i["name"]} FAILED to save')

    # for now we will replace the "BG" attribute url  with the raw image url
    bg_url = None
    target_code = "BG" 
    result = next((obj for obj in img_paths['masks'] if obj.get("code") == target_code), None)
    if result:
        # Load the image
        result['url'] = img_paths['rawImageSource']
        image_path = str(img_paths['rawImageSource'])  # Simple string copy  
        if do_rotation:      
            rotate_raw_img(image_path)
        # print("img_paths after processing: ", img_paths) 
    return img_paths

def rotate_raw_img(image_path):
    try:
        abs_path = os.path.join(current_app.root_path, f'static{image_path}' )
        img = PILImage.open(abs_path)

            # Rotate 90 degrees clockwise
            # PIL's rotate is counterclockwise, so we use -90 for clockwise
        img = img.rotate(-90, expand=True)
            # Note: expand=True ensures the entire image is visible after rotation

            # Save the rotated image
            # You can either overwrite the original or save to a new file
        img.save(abs_path, quality=95)

            # Close the images
        img.close()
    except Exception as e:
        print('Failed to rotate %s. Reason: %s' % (abs_path, e))
        
def process_image_path(img_paths, filename):
    
    url = url_for("static", filename=f"{current_app.config['TEMP_OUTPUT_FOLDER']}/{filename}")
    # example class attribute filename 3DA3BE74-0CAE-4BD6-906C-8E5C87FEC4E7_class_0_pred.png
    if '_class_' in filename:
        class_num = get_class_num(filename)
        attr = ATTR_MAP[class_num]
        attr['url'] = url
        img_paths['masks'].append(attr)
    # example raw filename 0891E28B-2E9F-476A-99FC-D8CEE7090AF2_raw.png
    elif '_raw' in filename:
        img_paths['rawImageSource'] = url
        bg_url = url
    # example pred filename 0891E28B-2E9F-476A-99FC-D8CEE7090AF2_pred.png
    elif '_pred' in filename:
        img_paths['predictionImageSource'] = url
    # example composited filename 0891E28B-2E9F-476A-99FC-D8CEE7090AF2_composited.png
    elif '_composited' in filename:
        img_paths['compositeImageSource'] = url    
   

    return img_paths

def get_class_num(filename):
    end = filename.index('.') - len(filename)  
    start = filename.index('_class_') + 7
    return filename[start:end]   
   
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get("ALLOWED_EXTENSIONS") 
