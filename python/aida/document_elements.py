"""
AIDA document elements container
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 January 2020"

from aida.container import Container
from aida.document_element import DocumentElement

class DocumentElements(Container):
    """
    AIDA document elements container
    """

    def __init__(self, logger):
        super().__init__(logger)
    
    def add_document_element(self, document_element):
        doceid = document_element.get('ID')
        self.document_elements.add(key = doceid, value = document_element)