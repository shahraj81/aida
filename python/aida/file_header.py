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
    File header for AIDA.
    """

    def __init__(self, logger, header_line):
        super().__init__(logger)
        self.logger = logger
        self.line = header_line
        self.columns = list(re.split(r'\t', header_line))
    
    def __str__(self, *args, **kwargs):
        return self.line