
from domain.constants import INDICATIONS, SURGERY_TYPES


def utility_processor():
    """Context processor with all template helpers"""
    
    def get_surgery_options():
        return [(code, label) for code, label in SURGERY_TYPES.items()]
    
    
    def get_indication_options():
        return [(code, label) for code, label in INDICATIONS.items()]
    
    return dict(
        get_surgery_options=get_surgery_options,
        get_indication_options=get_indication_options
    )

def register_context_processors(app):
    """Register all context processors"""
    app.context_processor(utility_processor)