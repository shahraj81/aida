"""
AIDA ERESpec for ontology files to serve as base class for entity, event and relation spec
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 February 2020"

from aida.object import Object

def unspecified(ere_type):
    if ere_type.lower() in ['unspecified', 'n/a', 'none', 'not present']:
        return True
    return False

class ERESpec(Object):
    """
    AIDA ERESpec for ontology files to serve as base class for entity, event and relation spec
    """
    def __init__(self, logger, entry):
        super().__init__(logger)
        self.entry = entry

    def get_raw_full_type(self):
        return '{}.{}.{}'.format(self.get('type'), self.get('subtype'), self.get('subsubtype'))

    def get_raw_full_type_ov(self):
        return '{}.{}.{}'.format(self.get('type_ov'), self.get('subtype_ov'), self.get('subsubtype_ov'))
    
    def get_cleaned_full_type(self):
        if unspecified(self.get('type')):
            return
        full_type = self.get('type')
        if not unspecified(self.get('subtype')):
            full_type = '{}.{}'.format(self.get('type'), self.get('subtype'))
        if not unspecified(self.get('subtype')) and not unspecified(self.get('subsubtype')):
            full_type = '{}.{}.{}'.format(self.get('type'), self.get('subtype'), self.get('subsubtype'))
        return full_type
    
    def get_cleaned_full_type_ov(self):
        if unspecified(self.get('type')):
            return
        full_type = self.get('type_ov')
        if not unspecified(self.get('subtype_ov')):
            full_type = '{}.{}'.format(self.get('type_ov'), self.get('subtype_ov'))
        if not unspecified(self.get('subtype_ov')) and not unspecified(self.get('subsubtype_ov')):
            full_type = '{}.{}.{}'.format(self.get('type_ov'), self.get('subtype_ov'), self.get('subsubtype_ov'))
        return full_type
    