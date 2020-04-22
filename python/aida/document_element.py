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
    AIDA document-element class.
    """

    def __init__(self, logger, id=None):
        super().__init__(logger)
        self.documents = Documents(logger)
        self.id = id