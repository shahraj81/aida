"""
AIDA class for graph query scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.scorer import Scorer

class GraphScorer(Scorer):
    """
    AIDA class for graph query scores.
    """
    def __init__(self, logger, runid, document_mappings, queries, response_set, assessments, queries_to_score):
        super().__init__(logger)