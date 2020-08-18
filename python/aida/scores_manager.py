"""
AIDA class for managing scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

# TODO: to be retired

from aida.object import Object
from aida.container import Container
from aida.coreferencemetric_scorer import CoreferenceMetricScorer
from aida.typemetric_scorer import TypeMetricScorer

import os

class ScoresManager(Object):
    """
    AIDA class for managing scores.
    """
    
    metrics = {
        'CoreferenceMetric': CoreferenceMetricScorer,
        'TypeMetric': TypeMetricScorer,
        }

    def __init__(self, logger, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator = None):
        super().__init__(logger)
        self.gold_responses = gold_responses
        self.system_responses = system_responses
        self.cluster_alignment = cluster_alignment
        self.cluster_self_similarities = cluster_self_similarities
        self.separator = separator
        self.scores = Container(logger)
        self.score_responses()

    def score_responses(self):
        for metric in self.get('metrics'):
            scorer = self.get('metrics')[metric](self.get('logger'),
                                    self.get('gold_responses'),
                                    self.get('system_responses'),
                                    self.get('cluster_alignment'),
                                    self.get('cluster_self_similarities'),
                                    self.get('separator'))
            self.get('scores').add(key=metric, value=scorer)

    def print_scores(self, output_directory):
        os.mkdir(output_directory)
        for metric in self.get('scores'):
            scores = self.get('scores').get(metric)
            output_file = '{}/{}-scores.txt'.format(output_directory, metric)
            scores.print_scores(output_file)