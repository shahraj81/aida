"""
AIDA class for class query scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.scorer import Scorer
from aida.class_score import ClassScore
from aida.score_printer import ScorePrinter

class ClassScorer(Scorer):
    """
    AIDA class for class query scores.
    """
    
    printing_specs = [{'name': 'ec',               'header': 'QID/EC',  'format': 's', 'justify': 'L'},
                      {'name': 'document_id',      'header': 'DocID',   'format': 's', 'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',   'format': 's', 'justify': 'L'},
                      {'name': 'num_ground_truth', 'header': 'GT',      'format': 'd', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'num_submitted',    'header': 'Sub',     'format': 'd', 'justify': 'R'},
                      {'name': 'num_pooled',       'header': 'Pooled',  'format': 'd', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'num_correct',      'header': 'Correct', 'format': 'd', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'num_redundant',    'header': 'Dup',     'format': 'd', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'num_incorrect',    'header': 'Incrct',  'format': 'd', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'num_counted',      'header': 'Cntd',    'format': 'd', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'num_right',        'header': 'Right',   'format': 'd', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'num_wrong',        'header': 'Wrong',   'format': 'd', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'num_ignored',      'header': 'Ignrd',   'format': 'd', 'justify': 'R', 'mean_format': '%4.2f'},
                      {'name': 'scoring_metric_1', 'header': 'SM-1',    'format': '.4f', 'justify': 'L'},
                      {'name': 'scoring_metric_2', 'header': 'SM-2',    'format': '.4f', 'justify': 'L'},
                      {'name': 'scoring_metric_3', 'header': 'SM-3',    'format': '.4f', 'justify': 'L'}]
    
    def __init__(self, logger, runid, document_mappings, queries, response_set, assessments, queries_to_score, separator=None):
        super().__init__(logger, runid, document_mappings, queries, response_set, assessments, queries_to_score, separator)
       
    def score_responses(self):
        
        scores = ScorePrinter(self.logger, self.printing_specs, self.separator)
        
        # TODO: add details
        
        for query_id in self.queries_to_score:
            for document_id in self.document_mappings.get('core_documents'):
                num_submitted = 150
                num_correct = 70
                num_incorrect = 30
                num_right = 60
                num_wrong = 40
                num_redundant = 10
                num_pooled = 100
                num_ignored = 50
                num_ground_truth = 100
                scoring_metric_1 = 0.8
                scoring_metric_2 = 0.7
                scoring_metric_3 = 0.6
                score = ClassScore(self.logger,
                                   self.runid,
                                   query_id,
                                   document_id,
                                   num_submitted,
                                   num_correct,
                                   num_incorrect,
                                   num_right,
                                   num_wrong,
                                   num_redundant,
                                   num_pooled,
                                   num_ignored,
                                   num_ground_truth,
                                   scoring_metric_1,
                                   scoring_metric_2,
                                   scoring_metric_3)
                scores.add(score)
        self.scores = scores
        
    def __str__(self):
        return self.get('scores').__str__()