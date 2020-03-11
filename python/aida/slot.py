"""
AIDA slot class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 January 2020"

from aida.object import Object

class Slot(Object):
    """
    AIDA slot class.
    """
    
    def __init__(self, logger, subject, slot_code, slot_type, argument, where):
        super().__init__(logger)
        self.subject = subject
        self.slot_code = slot_code
        self.slot_type = slot_type
        self.argument = argument
        self.where = where