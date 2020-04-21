"""
AIDA documents class
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 January 2020"

from aida.container import Container

class Documents(Container):
    """
    AIDA documents class
    """

    def __init__(self, logger):
        super().__init__(logger)