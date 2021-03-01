"""
AIDA class for managing scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.object import Object
from aida.container import Container

from aida.across_documents_correference_metric_scorer import AcrossDocumentsCoreferenceMetricScorer
from aida.argument_metric_v1_scorer import ArgumentMetricScorerV1
from aida.argument_metric_v2_scorer import ArgumentMetricScorerV2
from aida.coreference_metric_scorer import CoreferenceMetricScorer
from aida.frame_metric_scorer import FrameMetricScorer
from aida.temporal_metric_scorer import TemporalMetricScorer
from aida.type_metric_v1_scorer import TypeMetricScorerV1
from aida.type_metric_v2_scorer import TypeMetricScorerV2
from aida.type_metric_v3_scorer import TypeMetricScorerV3

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
            'TypeMetricV1': TypeMetricScorerV1,
            'TypeMetricV2': TypeMetricScorerV2,
            'TypeMetricV3': TypeMetricScorerV3,
            },
        'task2': {
            'AcrossDocumentsCoreferenceMetric': AcrossDocumentsCoreferenceMetricScorer
            }
        }

    def __init__(self, logger, task, arguments, separator=None):
        super().__init__(logger)
        self.task = task
        for key in arguments:
            self.set(key, arguments[key])
        self.metrics = self.task_metrics[task]
        self.separator = separator
        self.scores = Container(logger)
        self.score_responses()

    def score_responses(self):
        if self.get('task') == 'task1':
            for metric in self.get('metrics'):
                scorer = self.get('metrics')[metric](logger=self.get('logger'),
                                                     run_id=self.get('run_id'),
                                                     annotated_regions=self.get('annotated_regions'),
                                                     gold_responses=self.get('gold_responses'),
                                                     system_responses=self.get('system_responses'),
                                                     cluster_alignment=self.get('cluster_alignment'),
                                                     cluster_self_similarities=self.get('cluster_self_similarities'),
                                                     separator=self.get('separator'))
                self.get('scores').add(key=metric, value=scorer)
        if self.get('task') == 'task2':
            for metric in self.get('metrics'):
                scorer = self.get('metrics')[metric](logger=self.get('logger'),
                                                     run_id=self.get('run_id'),
                                                     cutoff=self.get('cutoff'),
                                                     normalize=self.get('normalize'),
                                                     weighted=self.get('weighted'),
                                                     responses=self.get('responses'),
                                                     assessments=self.get('assessments'),
                                                     queries_to_score=self.get('queries_to_score'),
                                                     separator=self.get('separator'))
                self.get('scores').add(key=metric, value=scorer)

    def print_scores(self, output_directory):
        os.mkdir(output_directory)
        for metric in self.get('scores'):
            scores = self.get('scores').get(metric)
            output_file = '{}/{}-scores.txt'.format(output_directory, metric)
            scores.print_scores(output_file)
            output_file = '{}/{}-ci.txt'.format(output_directory, metric)
            scores.print_confidence_intervals(output_file)