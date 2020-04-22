"""
AIDA document elements container.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 January 2020"

from aida.container import Container
from aida.document_element import DocumentElement

class DocumentElements(Container):
    """
    The container to hold document elements.
    """

    def __init__(self, logger):
        """
        Initializes this instance.
        """
        super().__init__(logger)
    
    def add_document_element(self, document_element):
        """
        Adds the document element to the container.
        """
        doceid = document_element.get('id')
        self.document_elements.add(key = doceid, value = document_element)