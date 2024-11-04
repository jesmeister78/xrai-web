
from sqlalchemy import engine
from flask import current_app
from sqlalchemy.orm import scoped_session, sessionmaker



def dict_to_entity(schema, data):
    sess = scoped_session(sessionmaker(bind=engine))
    return schema.load(data, session=sess)

def patch_from_json(payload, entity, replacements=None, exclusions=None):
    update_from_camel(payload["changes"], entity, replacements, exclusions)
    

def update_from_camel(camelDict, entity, replacements=None, exclusions=None):
    for key, value in camelDict.items(): 
        snakey = camel_to_snake(key)
        if replacements is not None:
            snakey = replace_multiple(snakey, replacements)
        # print(f"key: {key} snakey: {snakey}")
        if exclusions is None or snakey not in exclusions:
            if hasattr(entity, snakey): 
                # current_app.logger.info('update_from_camel: setting: <%s: %s>', snakey, value)
                setattr(entity, snakey, value)  
            else:
                # current_app.logger.info('update_from_camel: adding: <%s: %s>', snakey, value)
                entity[snakey] = value
    return entity
            
def camel_to_snake(string):
    return ''.join(['_' + char.lower() if char.isupper() else char for char in string]).lstrip('_')

def print_dict(dictionary):
    for key, value in dictionary.items():
        print(f"Key: {key}, Value: {value}")
        
def replace_multiple(text, replacements):
    """
    Replace multiple substrings in a string based on a dictionary of replacements.
    
    :param text: The original string to modify
    :param replacements: A dictionary where keys are strings to find and values are strings to replace with
    :return: The modified string
    """
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def pretty_print(obj: object, indent: int = 2) -> None:
    """
    Pretty prints a Python object with special handling for different types.
    
    Args:
        obj: Any Python object to print
        indent: Number of spaces for indentation (default: 2)
    """
    import json
    from typing import Any
    import weakref
    
    def custom_serializer(obj: Any) -> Any:
        """Handle special cases for JSON serialization."""
        # Handle weakrefs
        if isinstance(obj, weakref.ReferenceType):
            referred_obj = obj()
            return f"weakref to {type(referred_obj).__name__}" if referred_obj else "dead weakref"
            
        # Handle functions/methods/callables
        if callable(obj):
            try:
                return f"callable: {obj.__name__}"
            except AttributeError:
                return f"callable: {type(obj).__name__}"
                
        # Handle class instances
        if hasattr(obj, '__dict__'):
            # Filter out any weakrefs or non-serializable items from dict
            cleaned_dict = {}
            for k, v in obj.__dict__.items():
                try:
                    # Test if value is JSON serializable
                    json.dumps(v)
                    cleaned_dict[k] = v
                except (TypeError, OverflowError, ValueError):
                    cleaned_dict[k] = f"non-serializable ({type(v).__name__})"
            return cleaned_dict
            
        # Handle other special types
        if hasattr(obj, '__slots__'):
            return f"slots object: {type(obj).__name__}"
        
        # Handle any other non-serializable types
        return f"non-serializable: {type(obj).__name__}"
    
    try:
        print(
            json.dumps(
                obj,
                default=custom_serializer,
                indent=indent,
                ensure_ascii=False
            )
        )
    except (TypeError, OverflowError, ValueError) as e:
        print(f"Could not fully serialize object: {e}")
        # Fallback to built-in pretty printer
        import pprint
        pprint.pprint(obj, indent=indent)
        
# Example usage:
# example = {
#     "name": "John",
#     "age": 30,
#     "address": {
#         "street": "123 Main St",
#         "city": "Anytown"
#     },
#     "say_hello": lambda: "Hello!",
#     "undefined_value": None
# }
# pretty_print(example)