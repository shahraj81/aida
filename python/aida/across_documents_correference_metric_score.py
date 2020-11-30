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
    def __init__(self, logger, run_id, query_id, entity_id, average_precision, summary=False):
        super().__init__(logger)
        self.run_id = run_id
        self.query_id = query_id
        self.entity_id = entity_id
        self.average_precision = average_precision
        self.summary = summary