"""
AIDA class for negation metric score.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "13 September 2022"

from aida.score import Score

class NegationMetricScoreV1(Score):
    """
    AIDA class for negation metric score.
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.metatype_sortkey = '_ALL' if self.get('metatype') == 'ALL' else self.get('metatype')
        if not self.get('summary'):
            self.set_defaults()

    def set_defaults(self):
        defaults = {
            'summary': False,
            'gold_cluster_id': 'None',
            'system_cluster_id': 'None'
            }
        for key in defaults:
            if not self.get(key):
                self.set(key, defaults[key])