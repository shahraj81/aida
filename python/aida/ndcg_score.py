"""
AIDA class for NDCG-based task3 evaluation metric score.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "20 April 2022"

from aida.score import Score

class NDCGScore(Score):
    """
    AIDA class for NDCG-based task3 evaluation metric score.
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        if 'summary' not in kwargs:
            self.set('summary', False)

    def get_aggregate(self, field_name, aggregate_type):
        def mean_score(scores):
            sum_scores = 0
            for score in scores:
                sum_scores += score
            return sum_scores/len(scores)
        def macro(scores, field_name):
            score_values = []
            for score in scores.values():
                if int(score.get('ground_truth')):
                    score_values.append(score.get(field_name))
            return mean_score(score_values)
        retVal = self.get(field_name)
        if retVal:
            return retVal
        if field_name in ['precision', 'recall', 'gold_cluster_id', 'system_cluster_id', 'num_of_claims', 'num_of_unique_submitted_values', 'cutoff', 'ground_truth']:
            return ''
        if aggregate_type == 'ALL-Macro':
            return macro(self.get('elements'), field_name)
        return None