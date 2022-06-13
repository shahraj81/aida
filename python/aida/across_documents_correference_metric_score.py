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
    def __init__(self, logger, summary=False, **kwargs):
        super().__init__(logger)
        self.set('summary', summary)
        for key in kwargs:
            self.set(key, kwargs[key])

    def get_aggregate(self, field_name, aggregate_type):
        def mean_score(scores):
            sum_scores = 0
            for score in scores:
                sum_scores += score
            return sum_scores/len(scores)
        def macro(scores, field_name):
            score_values = []
            for score in scores.values():
                if int(score.get('num_rel_documents_counted')):
                    score_values.append(score.get(field_name))
            return mean_score(score_values)
        retVal = self.get(field_name)
        if retVal:
            return retVal
        if field_name != 'average_precision':
            return ''
        if aggregate_type == 'ALL-Macro':
            return macro(self.get('elements'), field_name)
        return None