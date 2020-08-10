"""
AIDA DocumentBoundary class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 January 2020"

from aida.span import Span
import re

class DocumentBoundary(Span):
    """
    AIDA DocumentBoundary class to be used for storing
    text document boundary, or image or video bounding box
    information.
    
    The DocumentBoundary inherits from the Span class, and
    adds a method called 'validate' for validating if a span
    passed as argument is inside the object boundary
    """

    def __init__(self, logger, start_x, start_y, end_x, end_y):
        """
        Initialize the DocumentBoundary object.
        """
        super().__init__(logger, start_x, start_y, end_x, end_y)
    
    def validate(self, span):
        """
        Validate if the span is inside the document boundary
        
        Arguments:
            span:
                span could be an aida.Span object, or a string of the
                form:
                    (start_x,start_y)-(end_x,end_y)

        Returns True if the span is inside the document, False otherwise.
        
        This method throws exception if span is not as mentioned above.
        """
        if isinstance(span, str):
            search_obj = re.search( r'^\((\d+),(\d+)\)-\((\d+),(\d+)\)$', span)
            if search_obj:
                start_x = search_obj.group(1)
                start_y = search_obj.group(2)
                end_x = search_obj.group(3)
                end_y = search_obj.group(4)
                span = Span(self.logger, start_x, start_y, end_x, end_y)
            else:
                raise Exception('{} is not of a form (start_x,start_y)-(end_x,end_y)'.format(span))
        
        if isinstance(span, Span):
            min_x, min_y, max_x, max_y = map(lambda arg:float(self.get(arg)),
                                 ['start_x', 'start_y', 'end_x', 'end_y'])
            sx, sy, ex, ey = map(lambda arg:float(span.get(arg)),
                                 ['start_x', 'start_y', 'end_x', 'end_y'])
            is_valid = False
            if min_x <= sx <= max_x and min_x <= ex <= max_x and min_y <= sy <= max_y and min_y <= ey <= max_y:
                is_valid = True
            return is_valid
        else:
            raise TypeError('{} called with argument of unexpected type'.format(isinstance.__name__))