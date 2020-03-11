"""
AIDA DocumentBoundaries class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 January 2020"

from aida.container import Container

import re

class DocumentBoundaries(Container):
    """
    AIDA DocumentBoundaries class.
    
    This class serves as the base class for:
        TextDocumentBoundaries
        ImageBoundaries
        KeyFrameBoundaries
    
    The derived classes will need to provide the implementation of
    corresponding load method.
    """

    def __init__(self, logger, filename):
        super().__init__(logger)
        self.filename = filename
        self.load()
        
    def get_BOUNDARY(self, span_string):
        """
        Given a span_string of the form:
            doceid:(start_x,start_y)-(end_x,end_y)
        Return the document boundary of the document element with
        ID=doceid
        """
        document_boundary = None
        search_obj = re.search( r'^(.*?):\((\d+),(\d+)\)-\((\d+),(\d+)\)$', span_string)
        if search_obj:
            doceid = search_obj.group(1)
            if self.exists(doceid):
                document_boundary = self.get(doceid)
        return document_boundary