"""
The class providing access to ImageBoundaries class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 January 2020"

from aida.document_boundaries import DocumentBoundaries
from aida.file_handler import FileHandler
from aida.document_boundary import DocumentBoundary
from os.path import splitext

class ImageBoundaries(DocumentBoundaries):
    """
    This class provides easy access to image boundaries, and is inherited from the
    DocumentBoundaries class which is a container customized for storing document
    boundaries, and providing methods to provide access to these document boundaries.
    """

    def __init__(self, logger, filename):
        """
        Initialize the ImageBoundaries object by calling the constructor of
        the parent DocumentBoundaries, passing it the logger and the filename.
        """
        super().__init__(logger, filename)
    
    def load(self):
        """
        load image boundary information.
        """
        for entry in FileHandler(self.logger, self.filename):
            start_x, start_y, end_x, end_y = [0, 0, 0, 0]
            document_element_id = splitext(entry.get('image_filename'))[0]
            entry.set('document_element_id', document_element_id)
            if entry.get('wxh'):
                end_x, end_y = entry.get('wxh').split('x')
            self.add(key=entry.get('document_element_id'),
                     value=DocumentBoundary(self.logger,
                                            start_x, 
                                            start_y, 
                                            end_x, 
                                            end_y))