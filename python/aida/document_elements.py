"""
The container used for storing document elements.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 January 2020"

from aida.container import Container

class DocumentElements(Container):
    """
    The container used for storing document elements.
    """

    def __init__(self, logger):
        """
        Initializes this instance.
        """
        super().__init__(logger)