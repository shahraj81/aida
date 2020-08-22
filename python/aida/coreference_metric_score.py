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
    def __init__(self, logger, run_id, document_id, precision, recall, f1, summary=False):
        super().__init__(logger)
        self.run_id = run_id
        self.document_id = document_id
        self.precision = precision
        self.recall = recall
        self.f1 = f1
        self.summary = summary