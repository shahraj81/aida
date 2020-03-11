"""
AIDA KeyFrameBoundaries class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 January 2020"

from aida.document_boundaries import DocumentBoundaries
from aida.file_handler import FileHandler
from aida.document_boundary import DocumentBoundary

class KeyFrameBoundaries(DocumentBoundaries):
    """
    AIDA KeyFrameBoundaries class.
    """

    def __init__(self, logger, filename):
        super().__init__(logger, filename)
    
    def load(self):
        """
        load keyframe boundary information.
        """
        for entry in FileHandler(self.logger, self.filename):
            start_x, start_y, end_x, end_y = [0, 0, 0, 0]
            if entry.get('wxh'):
                end_x, end_y = entry.get('wxh').split('x')
            self.add(key=entry.get('keyframeid'),
                     value=DocumentBoundary(self.logger,
                                            start_x, 
                                            start_y, 
                                            end_x, 
                                            end_y))