"""
AIDA entity specs for ontology files
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 February 2020"

from aida.ere_spec import ERESpec

class EntitySpec(ERESpec):
    def __init__(self, logger, entry):
        super().__init__(logger, entry)
        self.type = entry.get('Type')
        self.subtype = entry.get('Subtype')
        self.subsubtype = entry.get('Sub-subtype')
        self.type_ov = entry.get('Output Value for Type')
        self.subtype_ov = entry.get('Output Value for Subtype')
        self.subsubtype_ov = entry.get('Output Value for Sub-subtype')