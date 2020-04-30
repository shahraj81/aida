"""
Class representing relation and event slots.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 January 2020"

from aida.object import Object

class Slot(Object):
    """
    Class representing relation and event slots.
    """
    
    def __init__(self, logger, subject, slot_code, slot_type, argument, attribute, where):
        """
        Initialize the Slot.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object
            subject (aida.Mention)
            slot_code (str)
            slot_type (str)
            argument (aida.Mention)
            attribute (str)
            where (dict)
        """
        super().__init__(logger)
        self.subject = subject
        self.slot_code = slot_code
        self.slot_type = slot_type
        self.argument = argument
        self.attribute = attribute
        self.where = where

    def is_negated(self):
        """
        Returns True if the Slot is negated, False otherwise.
        """
        attributes = self.get('attribute')
        return attributes is not None and 'not' in attributes.split(',')

    def get_ID(self):
        """
        Gets the ID of the instance.

        The ID is the concatenation of the subject ID, slot type, and the argument ID, separated by colon ':'
        """
        return '{}:{}:{}'.format(self.get('subject').get('ID'), self.get('slot_type'), self.get('argument').get('ID'))