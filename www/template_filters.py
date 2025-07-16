# www/template_filters.py

from domain.constants import INDICATIONS, SURGERY_TYPES

def indication_label(indication_code):
    """Convert indication code(s) to display label(s)"""
    if not indication_code or not isinstance(indication_code, str):
        return ''
    
    try:
        # Split on comma, strip whitespace, and filter empty strings
        codes = [code.strip() for code in indication_code.split(',') if code.strip()]
        
        # Look up each code in the INDICATIONS dictionary
        labels = [INDICATIONS.get(code, code) for code in codes]
        
        # Join back with comma-space separator
        return ', '.join(labels)
    except Exception as e:
        # Log error and return original value as fallback
        print(f"Error processing indication codes '{indication_code}': {e}")
        return indication_code

def surgery_type_label(type_code):
    """Convert surgery type code to display label"""
    if not type_code or not isinstance(type_code, str):
        return ''
    return SURGERY_TYPES.get(type_code, type_code)




def register_template_filters(app):
    """Register all template filters with the Flask app"""
    app.jinja_env.filters['indication_label'] = indication_label
    app.jinja_env.filters['surgery_type_label'] = surgery_type_label