"""
AIDA encoding format to modality mappings class.
"""
from fileinput import filename

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "13 January 2020"

from aida.file_handler import FileHandler
from aida.container import Container

class Encodings(Container):
    """
    AIDA encoding format to modality mappings class.
    """

    def __init__(self, logger, filename):
        super().__init__(logger)
        self.logger = logger
        self.filename = filename
        self.load_data()
        
    def load_data(self):
        fh = FileHandler(self.logger, self.filename)
        for entry in fh.get('entries'):
            self.add(key=entry.get('encoding'), value=entry.get('modality'))