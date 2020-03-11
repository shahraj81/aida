"""
AIDA VideoBoundaries class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 February 2020"

from aida.document_boundaries import DocumentBoundaries
from aida.file_handler import FileHandler
from aida.document_boundary import DocumentBoundary
from os.path import splitext

class VideoBoundaries(DocumentBoundaries):
    """
    AIDA VideoBoundaries class.
    """

    def __init__(self, logger, filename):
        super().__init__(logger, filename)
    
    def load(self):
        """
        load video boundary information.
        """
        for entry in FileHandler(self.logger, self.filename):
            start_x, start_y, end_x, end_y = [0, 0, 0, 0]
            document_element_id = splitext(entry.get('video_filename'))[0]
            entry.set('document_element_id', document_element_id)
            if entry.get('length'):
                end_x = entry.get('length')
            self.add(key=entry.get('document_element_id'),
                     value=DocumentBoundary(self.logger,
                                            start_x, 
                                            start_y, 
                                            end_x, 
                                            end_y))