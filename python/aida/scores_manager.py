"""
AIDA class for managing scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

# TODO: to be retired

from aida.object import Object
from aida.class_scorer import ClassScorer
from aida.graph_scorer import GraphScorer

class ScoresManager(Object):
    """
    AIDA class for managing scores.
    """
    
    scorer = {
        'ClassQuery': ClassScorer,
        'GraphQuery': GraphScorer
        }

    def __init__(self, logger, runid, document_mappings, queries, response_set, assessments, queries_to_score, separator = None):
        super().__init__(logger)
        self.runid = runid
        self.document_mappings = document_mappings
        self.queries = queries
        self.response_set = response_set
        self.assessments = assessments
        self.query_type = queries.get('query_type')
        self.queries_to_score = queries_to_score
        self.separator = separator
        self.score_responses()
    
    def score_responses(self):
        logger, runid, document_mappings, queries, responses, assessments, queries_to_score, separator = map(lambda arg: self.get(arg),
                                                                                                  ['logger',
                                                                                                   'runid',
                                                                                                   'document_mappings',
                                                                                                   'queries',
                                                                                                   'responses',
                                                                                                   'assessments',
                                                                                                   'queries_to_score',
                                                                                                   'separator'
                                                                                                   ])
        
        self.scores = self.scorer[self.query_type](logger, runid, document_mappings, queries, responses, assessments, queries_to_score, separator)
    
    def __str__(self):
        return self.get('scores').__str__()