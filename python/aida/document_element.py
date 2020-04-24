"""
AIDA document-element class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 January 2020"

from aida.object import Object
from aida.documents import Documents

class DocumentElement(Object):
    """
    The document-element class.

    Along with its own ID (i.e. the document element it refers to), the object of this class contains a container holding its parent documents.
    """

    def __init__(self, logger, ID=None):
        """
        Initializes this instance.
        """
        super().__init__(logger)
        self.documents = Documents(logger)
        self.ID = ID

    def add_document(self, document):
        """
        Adds the document that are the parents of the document element represented by this instance
        """
        self.get('documents').add_member(document)