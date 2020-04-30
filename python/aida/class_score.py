"""
AIDA class for class query score.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.score import Score

class ClassScore(Score):
    """
    AIDA class for class query score.
    """
    def __init__(self, logger, run_id, query_id, document_id, num_submitted, num_correct, num_incorrect, num_right, num_wrong, num_redundant, num_pooled, num_ignored, num_ground_truth, scoring_metric_1, scoring_metric_2, scoring_metric_3):
        super().__init__(logger)
        self.ec = query_id
        self.run_id = run_id
        self.query_id = query_id
        self.document_id = document_id
        self.num_submitted = num_submitted
        self.num_correct = num_correct
        self.num_incorrect = num_incorrect
        self.num_right = num_right
        self.num_wrong = num_wrong
        self.num_redundant = num_redundant
        self.num_pooled = num_pooled
        self.num_ignored = num_ignored
        self.num_ground_truth = num_ground_truth
        self.scoring_metric_1 = scoring_metric_1
        self.scoring_metric_2 = scoring_metric_2
        self.scoring_metric_3 = scoring_metric_3