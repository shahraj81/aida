"""
AIDA class for type metric score.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.score import Score

class TypeMetricScore(Score):
    """
    AIDA class for type metric score.
    """
    def __init__(self, logger, run_id, document_id, metatype, gold_cluster_id, system_cluster_id, precision, recall, f1, summary=False):
        super().__init__(logger)
        self.run_id = run_id
        self.document_id = document_id
        self.metatype = metatype
        self.gold_cluster_id = gold_cluster_id if gold_cluster_id is not None else 'None'
        self.system_cluster_id = system_cluster_id if system_cluster_id is not None else 'None'
        self.precision = precision
        self.recall = recall
        self.f1 = f1
        self.summary = summary