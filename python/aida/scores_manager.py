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

from aida.argument_metric_v1_scorer import ArgumentMetricScorerV1
from aida.argument_metric_v2_scorer import ArgumentMetricScorerV2
from aida.coreference_metric_scorer import CoreferenceMetricScorer
from aida.frame_metric_scorer import FrameMetricScorer
from aida.temporal_metric_scorer import TemporalMetricScorer
from aida.type_metric_scorer import TypeMetricScorer

import os

class ScoresManager(Object):
    """
    AIDA class for managing scores.
    """

    task_metrics = {
        'task1': {
            'ArgumentMetricV1': ArgumentMetricScorerV1,
            'ArgumentMetricV2': ArgumentMetricScorerV2,
            'CoreferenceMetric': CoreferenceMetricScorer,
            'FrameMetric': FrameMetricScorer,
            'TemporalMetric': TemporalMetricScorer,
            'TypeMetric': TypeMetricScorer,
            }
        }

    def __init__(self, logger, task, arguments, separator = None):
        super().__init__(logger)
        for key in arguments:
            self.set(key, arguments[key])
        self.metrics = self.task_metrics[task]
        self.separator = separator
        self.scores = Container(logger)
        self.set_metrics()
        self.score_responses()

    def score_responses(self):
        for metric in self.get('metrics'):
            scorer = self.get('metrics')[metric](self.get('logger'),
                                    self.get('annotated_regions'),
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