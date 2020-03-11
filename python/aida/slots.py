"""
AIDA slots class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "8 January 2020"

from aida.container import Container

class Slots(Container):
    """
    AIDA slots class.
    """
    def __init__(self, logger):
        super().__init__(logger)
        
    def add_slot(self, slot):
        key = '{}:{}:{}'.format(slot.get('subject').get('id'), slot.get('slot_type'), slot.get('argument').get('id'))
        if key not in self:
            self.add(key=key, value=slot)
        else:
            self.logger.record_event('DUPLICATE_VALUE', key, slot.get('where'))