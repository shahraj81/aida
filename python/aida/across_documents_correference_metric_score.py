"""
AIDA class for across documents coreference metric score.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "23 November 2020"

from aida.score import Score

class AcrossDocumentsCoreferenceMetricScore(Score):
    """
    AIDA class for AIDA class for across documents coreference metric score.
    """
    def __init__(self, logger, summary=False, **kwargs):
        super().__init__(logger)
        self.set('summary', summary)
        for key in kwargs:
            self.set(key, kwargs[key])