"""
File header for AIDA.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "2 January 2020"

from aida.object import Object

import re

class FileHeader(Object):
    """
    The object represending the header of a tab separated file.
    """

    def __init__(self, logger, header_line):
        """
        Initializes the FileHeader using header_line.

        Arguments:
            logger (aida.Logger):
                the aida.Logger object.
            header_line (str):
                the line used to generate the FileHeader object.
        """
        super().__init__(logger)
        self.logger = logger
        self.line = header_line
        self.columns = list(re.split(r'\t', header_line))
    
    def __str__(self, *args, **kwargs):
        """
        Returns the string representation of the header.
        """
        return self.get('line')