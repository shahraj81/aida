"""
AIDA class for temporal metric score.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "27 August 2020"

from aida.score import Score

class TemporalMetricScore(Score):
    """
    AIDA class for type metric score.
    """
    def __init__(self, logger, run_id, document_id, gold_cluster_id, system_cluster_id, similarity, summary=False):
        super().__init__(logger)
        self.run_id = run_id
        self.document_id = document_id
        self.gold_cluster_id = gold_cluster_id if gold_cluster_id is not None else 'None'
        self.system_cluster_id = system_cluster_id if system_cluster_id is not None else 'None'
        self.similarity = similarity
        self.summary = summary