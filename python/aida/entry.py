"""
Class to hold a file entry.

NOTE: Each line in a file corresponds to an entry.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "2 January 2020"

from aida.object import Object

class Entry(Object):
    """
    Class to hold a file entry.
    """

    def __init__(self, logger, keys, values, where):
        super().__init__(logger)
        if len(keys) != len(values):
            logger.record_event('UNEXPECTED_NUM_COLUMNS', len(keys), len(values), where)
        self.where = where
        for i in range(len(keys)):
            self.set(keys[i], values[i])

    def get_filename(self):
        return self.get('where').get('filename')
    
    def get_lineno(self):
        return self.get('where').get('lineno')                 