"""
File handler for AIDA.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "2 January 2020"

from aida.object import Object
from aida.entry import Entry
from aida.file_header import FileHeader

import re

class FileHandler(Object):
    """
    File handler for AIDA.
    """

    def __init__(self, logger, filename, header=None, encoding=None):
        super().__init__(logger)
        self.encoding = encoding
        self.filename = filename
        self.header = header
        self.logger = logger
        self.entries = []
        self.load_file()
    
    def load_file(self):
        with open(self.filename, encoding=self.encoding) as file:
            for lineno, line in enumerate(file, start=1):
                if self.header is None:
                    self.header = FileHeader(self.logger, line.rstrip())
                else:
                    where = {'filename': self.filename, 'lineno': lineno}
                    entry = Entry(self.logger, self.header.columns, 
                                   line.rstrip('\r\n').split('\t', len(self.header.columns)-1), where)
                    entry.set('where', where)
                    entry.set('header', self.header)
                    entry.set('line', line)
                    self.entries.append(entry)
    
    def __iter__(self):
        return iter(self.entries)