"""
The class for storing information about a document.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 January 2020"

from aida.object import Object
from aida.document_elements import DocumentElements

class Document(Object):
    """
    The class for storing information about a document.
    """

    def __init__(self, logger, ID=None):
        """
        Initializes the document instance, setting the logger, and optionally its ID.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object
            ID (str):
                the string identifier of the document

        NOTE: the document contains a container to store document elements that
        comprise this document.
        """
        super().__init__(logger)
        self.document_elements = DocumentElements(logger)
        self.ID = ID
        self.logger = logger

    def add_document_element(self, document_element):
        """
        Adds the document element to this document.

        Arguments:
            document_element (aida.DocumentELement)
        """
        self.get('document_elements').add_member(document_element)
