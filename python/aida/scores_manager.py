"""
AIDA class for managing scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.object import Object
from aida.container import Container

from aida.across_documents_correference_metric_scorer_v2 import AcrossDocumentsCoreferenceMetricScorerV2
from aida.argument_metric_v1_scorer import ArgumentMetricScorerV1
from aida.argument_metric_v2_scorer import ArgumentMetricScorerV2
from aida.coreference_metric_scorer import CoreferenceMetricScorer
from aida.f1_v1a_scorer import F1ScorerV1A
from aida.f1_v2a_scorer import F1ScorerV2A
from aida.f1_v1b_scorer import F1ScorerV1B
from aida.f1_v2b_scorer import F1ScorerV2B
from aida.f1_v1c_scorer import F1ScorerV1C
from aida.f1_v2c_scorer import F1ScorerV2C
from aida.frame_metric_scorer import FrameMetricScorer
from aida.negation_metric_scorer import NegationMetricScorer
from aida.ndcg_v1_scorer import NDCGScorerV1
from aida.ndcg_v2_scorer import NDCGScorerV2
from aida.temporal_metric_scorer import TemporalMetricScorer
from aida.type_metric_v1_scorer import TypeMetricScorerV1
from aida.type_metric_v2_scorer import TypeMetricScorerV2
from aida.type_metric_v3_scorer import TypeMetricScorerV3
from aida.type_metric_v4_scorer import TypeMetricScorerV4

import os

class ScoresManager(Object):
    """
    AIDA class for managing scores.
    """

    task_metrics = {
        'task1': {
            # 'ArgumentMetricV1': ArgumentMetricScorerV1,
            # 'ArgumentMetricV2': ArgumentMetricScorerV2,
            'CoreferenceMetric': CoreferenceMetricScorer,
            # 'FrameMetric': FrameMetricScorer,
            # 'TemporalMetric': TemporalMetricScorer,
            # 'TypeMetricV1': TypeMetricScorerV1,
            # 'TypeMetricV2': TypeMetricScorerV2,
            # 'TypeMetricV3': TypeMetricScorerV3,
            'NegationMetric': NegationMetricScorer,
            'TypeMetricV4': TypeMetricScorerV4,
            },
        'task2': {
            'AcrossDocumentsCoreferenceMetricV2': AcrossDocumentsCoreferenceMetricScorerV2,
            },
        'task3': {
            'F1ScorerV1A': F1ScorerV1A,
            'F1ScorerV2A': F1ScorerV2A,
            'F1ScorerV1B': F1ScorerV1B,
            'F1ScorerV2B': F1ScorerV2B,
            'F1ScorerV1C': F1ScorerV1C,
            'F1ScorerV2C': F1ScorerV2C,
            'NDCGScorerV1': NDCGScorerV1,
            'NDCGScorerV2': NDCGScorerV2,
            }
        }

    def __init__(self, logger, task, arguments):
        super().__init__(logger)
        self.task = task
        for key in arguments:
            self.set(key, arguments[key])
        self.metrics = self.task_metrics[task]
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
                                                     mention_alignment=self.get('mention_alignment'),
                                                     cluster_self_similarities=self.get('cluster_self_similarities'),
                                                     type_similarities=self.get('type_similarities'))
                self.get('scores').add(key=metric, value=scorer)
        elif self.get('task') == 'task2':
            for metric in self.get('metrics'):
                scorer = self.get('metrics')[metric](logger=self.get('logger'),
                                                     run_id=self.get('run_id'),
                                                     cutoff=self.get('cutoff'),
                                                     normalize=self.get('normalize'),
                                                     weighted=self.get('weighted'),
                                                     responses=self.get('responses'),
                                                     assessments=self.get('assessments'),
                                                     queries_to_score=self.get('queries_to_score'))
                self.get('scores').add(key=metric, value=scorer)
        elif self.get('task') == 'task3':
            for metric in self.get('metrics'):
                scorer = self.get('metrics')[metric](logger=self.get('logger'),
                                                     run_id=self.get('run_id'),
                                                     responses_dir=self.get('responses_dir'),
                                                     assessments=self.get('assessments'),
                                                     queries_to_score=self.get('queries_to_score'))
                self.get('scores').add(key=metric, value=scorer)

    def print_scores(self, output_directory):
        os.mkdir(output_directory)
        for metric in self.get('scores'):
            scores = self.get('scores').get(metric)
            output_file = '{}/{}-scores.txt'.format(output_directory, metric)
            scores.print_scores(output_file, 'pretty')
            output_file = '{}/{}-scores.tab'.format(output_directory, metric)
            scores.print_scores(output_file, 'tab')