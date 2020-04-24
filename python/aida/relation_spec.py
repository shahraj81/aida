"""
Specifications of a relation as taken from ontology.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 February 2020"

from aida.ere_spec import ERESpec
from aida.container import Container
from aida.argument_spec import ArgumentSpec

class RelationSpec(ERESpec):
    """
    Specifications of a relation as taken from ontology.
    """
    def __init__(self, logger, entry):
        """
        Initialize the specifications of a relation taken from the entry corresponding to a line
        as read from ontology.
        """
        super().__init__(logger, entry)
        self.arguments = Container(logger)
        self.annotation_id = entry.get('AnnotIndexID')
        self.type = entry.get('Type')
        self.subtype = entry.get('Subtype')
        self.subsubtype = entry.get('Sub-Subtype')
        self.type_ov = entry.get('Output Value for Type')
        self.subtype_ov = entry.get('Output Value for Subtype')
        self.subsubtype_ov = entry.get('Output Value for Sub-Subtype')
        for arg_num in range(1, 3):
            self.get('arguments').add(ArgumentSpec(logger, entry, arg_num), 'arg{}'.format(arg_num))
    
    