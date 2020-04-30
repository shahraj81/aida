"""
Class to hold a line in a tab-separated file.

NOTE: Each line in a file corresponds to an entry.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "2 January 2020"

from aida.object import Object

class Entry(Object):
    """
    The Entry represents a line in a tab separated file.
    """

    def __init__(self, logger, keys, values, where):
        """
        Initializes this instance.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object.
            keys (list of str):
                the list representing header fields.
            values (list of str):
                the list representing values corresponding to the keys.
            where (dict):
                a dictionary containing the following two keys representing the file location:
                    filename
                    lineno

        NOTE: The length of keys and values must match.
        """
        super().__init__(logger)
        if len(keys) != len(values):
            logger.record_event('UNEXPECTED_NUM_COLUMNS', len(keys), len(values), where)
        self.where = where
        for i in range(len(keys)):
            self.set(keys[i], values[i].strip())

    def get_filename(self):
        """
        Gets the name of the file which this instance corresponds to.
        """
        return self.get('where').get('filename')
    
    def get_lineno(self):
        """
        Gets the line number which this instance corresponds to.
        """
        return self.get('where').get('lineno')