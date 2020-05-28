"""
AIDA base class for query-specific derived score class.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.object import Object

class Score(Object):
    """
    AIDA base class for query-specific derived score class.
    """
    def __init__(self, logger):
        super().__init__(logger)
        
    def get_num_counted(self):
        return self.get('num_right') + self.get('num_wrong')