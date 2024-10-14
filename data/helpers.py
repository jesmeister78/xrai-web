
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
        print(f"key: {key} snakey: {snakey}")
        if exclusions is None or snakey not in exclusions:
            if hasattr(entity, snakey): 
                current_app.logger.info('update_from_camel: setting: <%s: %s>', snakey, value)
                setattr(entity, snakey, value)  
            else:
                current_app.logger.info('update_from_camel: adding: <%s: %s>', snakey, value)
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