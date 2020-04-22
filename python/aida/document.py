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
    The document class
    """

    def __init__(self, logger, id=None):
        """
        Initializes the document instance, setting the logger, and optionally its ID.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object
            id (str):
                the string identifier of the document

        NOTE: the document contains a container to store document elements that
        comprise this document.
        """
        super().__init__(logger)
        self.document_elements = DocumentElements(logger)
        self.id = id
        self.logger = logger

    def add_document_element(self, document_element):
        """
        Adds the document element to this document.

        Arguments:
            document_element (aida.DocumentELement)
        """
        doceid = document_element.get('id')
        self.document_elements.add(key = doceid, value = document_element)