"""
File handler for reading tab-separated files.
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
    File handler for reading tab-separated files.
   """

    def __init__(self, logger, filename, header=None, encoding=None):
        """
        Initializes this instance.
        Arguments:
            logger (aida.Logger):
                the aida.Logger object
            filename (str):
                the name of the file including the path
            header (aida.Header or None):
                if provided, this header will be used for the file,
                otherwise the header will be read from the first line.
            encoding (str or None):
                the encoding to be used for opening the file.
        """
        super().__init__(logger)
        self.encoding = encoding
        self.filename = filename
        self.header = header
        self.logger = logger
        # lines from the file are read into entries (aida.Entry)
        self.entries = []
        self.load_file()
    
    def load_file(self):
        """
        Load the file.
        """
        with open(self.get('filename'), encoding=self.get('encoding')) as file:
            for lineno, line in enumerate(file, start=1):
                if self.get('header') is None:
                    self.header = FileHeader(self.get('logger'), line.rstrip())
                else:
                    where = {'filename': self.get('filename'), 'lineno': lineno}
                    entry = Entry(self.get('logger'), self.get('header').get('columns'),
                                   line.rstrip('\r\n').split('\t', len(self.get('header').get('columns'))-1), where)
                    entry.set('where', where)
                    entry.set('header', self.get('header'))
                    entry.set('line', line)
                    self.get('entries').append(entry)
    
    def __iter__(self):
        """
        Returns iterator over entries.
        """
        return iter(self.get('entries'))