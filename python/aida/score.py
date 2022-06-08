"""
AIDA base class for query-specific derived score class.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.object import Object

class Score(Object):
    """
    AIDA base class for query-specific derived score class.
    """
    def __init__(self, logger):
        super().__init__(logger)

    def get_aggregate(self, field_name, aggregate_type):
        def mean_score(scores):
            sum_scores = 0
            for score in scores:
                sum_scores += score
            return sum_scores/len(scores)
        def micro(scores, field_name):
            return mean_score([s.get(field_name) for s in scores.values()])
        def macro(scores, field_name):
            document_scores = {}
            for score in scores.values():
                document_id = score.get('document_id')
                if document_id not in document_scores:
                    document_scores[document_id] = []
                document_scores[document_id].append(score.get(field_name))
            count = 0
            sum_score = 0
            for document_id in document_scores:
                count += 1
                sum_score += mean_score(document_scores[document_id])
            return sum_score/count
        retVal = self.get(field_name)
        if retVal:
            return retVal
        if field_name == 'document_id':
            return aggregate_type
        if field_name in ['precision', 'recall', 'gold_cluster_id', 'system_cluster_id', 'num_of_claims', 'num_of_unique_submitted_values', 'cutoff', 'ground_truth']:
            return ''
        if aggregate_type == 'ALL-Micro':
            return micro(self.get('elements'), field_name)
        if aggregate_type == 'ALL-Macro':
            return macro(self.get('elements'), field_name)
        return None