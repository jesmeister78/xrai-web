from pprint import pprint
from sqlalchemy.orm import selectinload
from datetime import datetime
import os
from typing import Dict, List, Optional
from uuid import UUID
from werkzeug.utils import secure_filename
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
from PIL import Image as PILImage
from flask import current_app, url_for

from domain import db
from domain.entities import ClassMask, Image
from domain.helpers import patch_from_json, print_dict, update_from_camel, pretty_print
from domain.schemas import ImageSchema
from domain.constants import ATTR_MAP
from xrai_engine.image_processor import ImageProcessor

class ImageService:
    def __init__(self, db_session=None):
        """
        Initialize UserService with optional database session.
        
        Args:
            db_session: SQLAlchemy session to use. If None, uses default db.session
        """
        self.db = db_session or db.session

    def get_images(self): 
        try:
            images = db.session.execute(db.select(Image).order_by(Image.img_timestamp)).scalars()
            return images
        except Exception as e:
            print(str(e))

    def get_Images_for_procedure(self, proc_id: UUID) -> List[Image]:
        """
        Retrieve images for a specific proc from the database.
        
        Args:
            proc_id: The UUID of the proc
        Returns:
            List of Image objects
        """
        try:
            images = (
                db.session.query(Image)
                .filter(Image.procedure_id == proc_id)
                .order_by(Image.img_timestamp)
                .all()
            )
            print("Successfully retrieved Images from database")
            pprint(images)
            return images

        except SQLAlchemyError as e:
            print(f"Database error occurred: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            raise

    def delete_image_by_id(self, image_id: UUID) -> bool:
        """
        Delete a single image by its ID.
        
        Args:
            image_id: The UUID of the image to delete
            
        Returns:
            bool: True if deletion was successful, False if image not found
            
        Raises:
            SQLAlchemyError: If there's a database error during deletion
        """
        try:
            image = db.session.query(Image).filter(Image.id == image_id).first()
            
            if not image:
                print(f"Image with id {image_id} not found")
                return False
                
            db.session.delete(image)
            db.session.commit()
            print(f"Successfully deleted image with id {image_id}")
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error occurred while deleting image: {str(e)}")
            raise
        except Exception as e:
            db.session.rollback()
            print(f"Unexpected error occurred while deleting image: {str(e)}")
            raise

    def delete_images_by_procedure_id(self, procedure_id: UUID) -> int:
        """
        Delete all images associated with a specific procedure ID.
        
        Args:
            procedure_id: The UUID of the procedure whose images should be deleted
            
        Returns:
            int: Number of images deleted
            
        Raises:
            SQLAlchemyError: If there's a database error during deletion
        """
        try:
            # Query to delete all images with the given procedure_id
            result = (
                db.session.query(Image)
                .filter(Image.procedure_id == procedure_id)
                .delete(synchronize_session=False)
            )
            
            db.session.commit()
            print(f"Successfully deleted {result} images for procedure {procedure_id}")
            return result
            
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error occurred while deleting images: {str(e)}")
            raise
        except Exception as e:
            db.session.rollback()
            print(f"Unexpected error occurred while deleting images: {str(e)}")
            raise
        
    
    def get_images_from_path(self, path: str) -> List[str]:
        """Get all valid images from a directory path"""
        ALLOWED_EXTENSIONS = {'.png', '.jpeg', '.jpg'}
        
        full_path = os.path.join(current_app.root_path, path)
        files = os.listdir(full_path)
        
        images = [file for file in files if os.path.splitext(file)[1].lower() in ALLOWED_EXTENSIONS]
        images = [os.path.join(path, file).replace('static/', '') for file in images]
        
        return images

    def clear_processed_images(self) -> None:
        """Clear all processed images from the staging folder"""
        folder = os.path.join(current_app.root_path, 'static', 'images', 'processed')
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    def allowed_file(self, filename: str) -> bool:
        """Check if a filename has an allowed extension"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config.get("ALLOWED_EXTENSIONS")

    def save_uploaded_file(self, file, form_data: dict) -> Image:
        """Save an uploaded file and create an Image record"""
        filename = secure_filename(file.filename)
        path = os.path.join('static', 'images', filename)
        file.save(os.path.join(current_app.root_path, path))
        
        image: Image = ImageSchema().load(form_data, session=self.db)
        image.raw_img_src = f"/images/{filename}"
        
        self.db.add(image)
        self.db.commit()
        
        return image

    def process_and_update_image(self, image_id: UUID) -> Image:
        """Process an existing image and update its record"""
        try:
            image = self.db.query(Image).filter(Image.id == image_id).one()
            processed_image_data = self.process_image(image.id, image.procedure_id, False)
            processed_image_data["labels_img_src"] = ""
            
            with self.db.no_autoflush:
                update_from_camel(processed_image_data, image, 
                                replacements={"image": "img", "source": "src"}, 
                                exclusions=["masks"])
                
                for mask in processed_image_data["masks"]:
                    mask_entity: ClassMask = update_from_camel(mask, ClassMask(), exclusions=["details"])
                    mask_entity.image_id = image.id
                    self.db.add(mask_entity)
                    image.masks.append(mask_entity)
            
            self.db.commit()
            return image
            
        except NoResultFound:
            raise NoResultFound(f"No Image found with id {image_id}")
        except Exception as e:
            self.db.rollback()
            raise e

    def process_image(self, img_id: UUID, proc_id: UUID, do_rotation: bool = True) -> Dict:
        """Process an image through the image processor"""
        experiment_folder = os.path.join(current_app.config['APP_ROOT_FOLDER'], 
                                       current_app.config['EXPERIMENT_FOLDER'])
        experiment_name = current_app.config['EXPERIMENT_NAME']
        config_folder = os.path.join(current_app.config['APP_ROOT_FOLDER'], 
                                   current_app.config['CONFIG_FOLDER'])
        
        imageProcessor = ImageProcessor(experiment_name, experiment_folder, config_folder, 0)
        raw_mask_comp = imageProcessor.processImage(0, False, do_rotation)
        
        processed_image = {
            "id": img_id,
            "procedureId": proc_id,
            "imageTimestamp": datetime.now()
        } | self.save_image_files(raw_mask_comp, do_rotation)
        
        self.delete_image_file(str(processed_image["id"]))
        return processed_image

    def save_image_files(self, img_arr: List[Dict], do_rotation: bool) -> Dict:
        """Save processed image files and return their paths"""
        img_paths = {'masks': []}
        
        for i in img_arr:
            filename = secure_filename(i['name'])
            img_file = i['img']
            img_url = url_for("static", filename=f"{current_app.config['TEMP_OUTPUT_FOLDER']}/{filename}")
            img_paths = self._process_image_path(img_paths, filename)
            
            save_path = os.path.join(current_app.root_path, 'static', 'images', 'processed', filename)
            img_file.save(save_path)

        target_code = "BG"
        result = next((obj for obj in img_paths['masks'] if obj.get("code") == target_code), None)
        if result:
            result['url'] = img_paths['rawImageSource']
            if do_rotation:
                self._rotate_raw_img(img_paths['rawImageSource'])
                
        return img_paths

    def _process_image_path(self, img_paths: Dict, filename: str) -> Dict:
        """Process image paths and update the paths dictionary"""
        url = url_for("static", filename=f"{current_app.config['TEMP_OUTPUT_FOLDER']}/{filename}")
        
        if '_class_' in filename:
            class_num = self._get_class_num(filename)
            attr = ATTR_MAP[class_num]
            attr['url'] = url
            img_paths['masks'].append(attr)
        elif '_raw' in filename:
            img_paths['rawImageSource'] = url
        elif '_pred' in filename:
            img_paths['predictionImageSource'] = url
        elif '_composited' in filename:
            img_paths['compositeImageSource'] = url
        
        return img_paths

    def _rotate_raw_img(self, image_path: str) -> None:
        """Rotate a raw image 90 degrees clockwise"""
        try:
            abs_path = os.path.join(current_app.root_path, f'static{image_path}')
            with PILImage.open(abs_path) as img:
                img = img.rotate(-90, expand=True)
                img.save(abs_path, quality=95)
        except Exception as e:
            print('Failed to rotate %s. Reason: %s' % (abs_path, e))

    def _get_class_num(self, filename: str) -> str:
        """Extract class number from filename"""
        end = filename.index('.') - len(filename)
        start = filename.index('_class_') + 7
        return filename[start:end]

    def delete_image_file(self, filename: str, raw_only: bool = True) -> None:
        """Delete an image file from the filesystem"""
        if not raw_only and 'processed/' not in filename:
            self.delete_image_file(f"processed/{filename}")
        
        folder = os.path.join(current_app.root_path, 'static', 'images')
        file_path = os.path.join(folder, filename)
        
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    def patch_image(self, image_id: UUID, patch_data: Dict) -> Image:
        """Patch an existing image with new data"""
        image = self.db.get(Image, image_id)
        patch_from_json(patch_data, image)
        self.db.commit()
        return image