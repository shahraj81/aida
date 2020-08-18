"""
AIDA class for coreference metric scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "17 August 2020"

from aida.scorer import Scorer
from aida.coreferencemetric_score import CoreferenceMetricScore
from aida.score_printer import ScorePrinter

class CoreferenceMetricScorer(Scorer):
    """
    AIDA class for class query scores.
    """
    
    printing_specs = [{'name': 'document_id',      'header': 'DocID',   'format': 's', 'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',   'format': 's', 'justify': 'L'},
                      {'name': 'precision',        'header': 'Prec',    'format': '6.4f', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'recall',           'header': 'Recall',  'format': '6.4f', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'f1',               'header': 'F1',      'format': '6.4f', 'justify': 'R', 'mean_format': '%4.2f'}]

    def __init__(self, logger, gold_responses, system_responses, cluster_alignment, separator=None):
        super().__init__(logger, gold_responses, system_responses, cluster_alignment, separator)

    def get_core_documents(self):
        return self.get('gold_responses').get('document_mappings').get('core_documents')

    def score_responses(self):
        scores = ScorePrinter(self.logger, self.printing_specs, self.separator)

        # TODO: add details

        for document_id in self.get('core_documents'):
            precision = 1
            recall = 1
            f1 = 1
            score = CoreferenceMetricScore(self.logger,
                                   self.get('runid'),
                                   document_id,
                                   precision,
                                   recall,
                                   f1)
            scores.add(score)
        self.scores = scores

    def print_scores(self, filename):
        fh = open(filename, 'w')
        fh.write(self.__str__())
        fh.close()

    def __str__(self):
        return self.get('scores').__str__()