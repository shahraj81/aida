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

    def __init__(self, logger, runid, document_mappings, queries, response_set, assessments, queries_to_score, separator=None):
        super().__init__(logger)
        self.runid = runid
        self.document_mappings = document_mappings
        self.queries = queries
        self.response_set = response_set
        self.assessments = assessments
        self.queries_to_score = queries_to_score
        self.separator = separator
        self.score_responses()