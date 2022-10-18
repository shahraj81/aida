"""
AIDA class for type-role-filler used for argument metric scoring.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 September 2020"

from aida.object import Object

class TypeRoleFiller(Object):
    """
    AIDA class for type-role-filler used for argument metric scoring.
    """
    def __init__(self, logger):
        super().__init__(logger)

    def update(self, key, value, single_valued=False):
        if single_valued:
            if self.get(key) is None:
                self.set(key, value)
            else:
                if self.get(key) != value:
                    self.record_event('MULTIPLE_VALUES', key, self.get('document_id'), self.get('trf_id'), self.get(key), value)
        else:
            if self.get(key) is None:
                self.set(key, set())
            if isinstance(value, set):
                self.get(key).update(value)
            else:
                self.get(key).add(value)