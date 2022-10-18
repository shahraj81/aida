"""
AIDA class for negation metric score.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "25 September 2022"

from aida.score import Score

class NegationMetricScoreV2(Score):
    """
    AIDA class for negation metric score.
    """
    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.metatype_sortkey = '_ALL' if self.get('metatype') == 'ALL' else self.get('metatype')
        if not self.get('summary'):
            self.set_defaults()

    def set_defaults(self):
        defaults = {
            'summary': False,
            'gold_cluster_id': 'None',
            'system_cluster_id': 'None'
            }
        for key in defaults:
            if not self.get(key):
                self.set(key, defaults[key])

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
        def sum_fieldvalues(scores, field_name):
            retVal = 0
            for score in scores.values():
                retVal += score.get(field_name)
            return retVal
        def precision(true_positive, false_positive, false_negative):
            return true_positive / (true_positive + false_positive) if (true_positive + false_positive) else 0
        def recall(true_positive, false_positive, false_negative):
            return true_positive / (true_positive + false_negative) if (true_positive + false_negative) else 0
        def f1(true_positive, false_positive, false_negative):
            p = precision(true_positive, false_positive, false_negative)
            r = recall(true_positive, false_positive, false_negative)
            return 2 * p * r / (p + r) if (p + r) else 0
        retVal = self.get(field_name)
        if retVal:
            return retVal
        if field_name == 'document_id':
            return aggregate_type
        if field_name in ['gold_cluster_id', 'system_cluster_id', 'num_of_claims', 'num_of_unique_submitted_values', 'cutoff', 'ground_truth']:
            return ''
        if aggregate_type == 'ALL-Micro':
            if field_name in ['precision', 'recall', 'f1']:
                true_positive = sum_fieldvalues(self.get('elements'), 'true_positive')
                false_positive = sum_fieldvalues(self.get('elements'), 'false_positive')
                false_negative = sum_fieldvalues(self.get('elements'), 'false_negative')
                if field_name == 'precision': return precision(true_positive, false_positive, false_negative)
                if field_name == 'recall': return recall(true_positive, false_positive, false_negative)
                if field_name == 'f1': return f1(true_positive, false_positive, false_negative)
            return micro(self.get('elements'), field_name)
        if aggregate_type == 'ALL-Macro':
            if field_name in ['precision', 'recall']: return ''
            return macro(self.get('elements'), field_name)
        return None

    def get_precision(self):
        true_positive = self.get('true_positive')
        false_positive = self.get('false_positive')
        if true_positive is not None and false_positive is not None:
            return true_positive / (true_positive + false_positive) if (true_positive + false_positive) else 0

    def get_recall(self):
        true_positive = self.get('true_positive')
        false_negative = self.get('false_negative')
        if true_positive is not None and false_negative is not None:
            return true_positive / (true_positive + false_negative) if (true_positive + false_negative) else 0

    def get_f1(self):
        precision = self.get('precision')
        recall = self.get('recall')
        if precision is not None and recall is not None:
            return 2 * precision * recall / (precision + recall) if (precision + recall) else 0