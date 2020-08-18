"""
AIDA Scorer class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.object import Object

class Scorer(Object):
    """
    AIDA Scorer class.
    """

    def __init__(self, logger, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator=None):
        super().__init__(logger)
        self.runid = system_responses.get('runid')
        self.gold_responses = gold_responses
        self.system_responses = system_responses
        self.cluster_alignment = cluster_alignment
        self.cluster_self_similarities = cluster_self_similarities
        self.separator = separator
        self.score_responses()