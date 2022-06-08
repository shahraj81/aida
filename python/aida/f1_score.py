"""
AIDA class for F1-based task3 evaluation metric score.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "6 June 2022"

from aida.score import Score

class F1Score(Score):
    """
    AIDA class for F1-based task3 evaluation metric score.
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        if 'summary' not in kwargs:
            self.set('summary', False)