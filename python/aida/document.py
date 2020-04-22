"""
AIDA document class
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 January 2020"

from aida.container import Container
from aida.document_elements import DocumentElements

class Document(Container):
    """
    AIDA document class
    """

    def __init__(self, logger, id=None):
        super().__init__(logger)
        self.document_elements = DocumentElements(logger)
        self.id = id
        self.logger = logger
    
    def add_document_element(self, document_element):
        doceid = document_element.get('id')
        self.document_elements.add(key = doceid, value = document_element)