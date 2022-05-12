"""
AIDA class for NDCG-based task3 evaluation metric score.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "20 April 2022"

from aida.score import Score

class NDCGScore(Score):
    """
    AIDA class for NDCG-based task3 evaluation metric score.
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        if 'summary' not in kwargs:
            self.set('summary', False)