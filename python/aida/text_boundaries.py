"""
The class providing access to TextDocumentBoundaries.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 January 2020"

from aida.document_boundaries import DocumentBoundaries
from aida.file_handler import FileHandler
from aida.document_boundary import DocumentBoundary

class TextBoundaries(DocumentBoundaries):
    """
    This class provides easy access to text document boundaries, and is inherited
    from the DocumentBoundaries class which is a container customized for storing
    document boundaries, and providing methods to provide access to these document
    boundaries.
    """

    def __init__(self, logger, filename):
        """
        Initialize TextDocumentBoundaries.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object
            filename (str):
                the file containing information about boundaries of text documents.
        """
        super().__init__(logger, filename)
    
    def load(self):
        """
        Read the sentence boundary file to load document boundary
        information.
        """
        for entry in FileHandler(self.logger, self.filename):
            doceid, start_char, end_char = map(
                    lambda arg: entry.get(arg), 
                    'doceid,start_char,end_char'.split(','))
            document_boundary = self.get(doceid, 
                                         default=DocumentBoundary(self.logger,
                                                                  start_char, 0, end_char, 0))
            tb_start_char = document_boundary.get('start_x')
            tb_end_char = document_boundary.get('end_x')
            if int(start_char) < int(tb_start_char):
                document_boundary.set('start_x', start_char)
            if int(end_char) > int(tb_end_char):
                document_boundary.set('end_x', end_char)