"""
AIDA class for coreference metric score.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "17 August 2020"

from aida.score import Score

class CoreferenceMetricScore(Score):
    """
    AIDA class for coreference metric score.
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        if 'summary' not in kwargs:
            self.set('summary', False)
        self.metatype_sortkey = '_ALL' if self.get('metatype') == 'ALL' else self.get('metatype')