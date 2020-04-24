"""
Span class to be used for storing a text span, or an image or video bounding box.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 January 2020"

from aida.object import Object

class Span(Object):
    """
    Span class to be used for storing a text span, or an image or video bounding box.

    TODO: Update this class for future use of the audio-only bounding box.
    """

    def __init__(self, logger, start_x, start_y, end_x, end_y):
        """
        Initialize the Span object.
        
        Arguments:
            logger (aida.Logger):
                the aida.Logger object
            start_x (string):
                the start character position of a text document, or
                the top-left-x coordinate for an image
            start_y (string):
                zero ('0') for a text document, or
                the top-left-y coordinate for an image
            end_x (string):
                the end character position of a text document, or
                the bottom-right-x coordinate for an image
            end_y (string):
                zero ('0') for a text document, or
                the bottom-right-y coordinate for an image
        """
        super().__init__(logger)
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
    
    def __str__(self, *args, **kwargs):
        """
        Return a string containing the bounding box in the form:
            START-END
        where
            START=(start_x,start_y)
            END=(end_x,end_y)
        """
        return "{}-{}".format(self.get('START'), self.get('END'))

    def get_START(self):
        """
        Return a string containing the start of the bounding box 
        in the form:
            (start_x,start_y)
        """        
        return "({},{})".format(self.start_x, self.start_y)
    
    def get_END(self):
        """
        Return a string containing the end of the bounding box 
        in the form:
            (end_x,end_y)
        """        
        return "({},{})".format(self.end_x, self.end_y)