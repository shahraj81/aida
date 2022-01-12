"""
Class for variant # 1 of the type metric scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.type_metric_v1_score import TypeMetricScoreV1
from aida.utility import get_precision_recall_and_f1, get_augmented_types_utility, multisort

class TypeMetricScorerV1(Scorer):
    """
    Class for variant # 1 of the type metric scores.

    This variant of the scorer considers all types asserted on the cluster as a set, and uses this set to compute
    precision, recall and F1.
    """

    printing_specs = [{'name': 'document_id',      'header': 'DocID',           'format': 's',    'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',           'format': 's',    'justify': 'L'},
                      {'name': 'language',         'header': 'Language',        'format': 's',    'justify': 'L'},
                      {'name': 'metatype',         'header': 'Metatype',        'format': 's',    'justify': 'L'},
                      {'name': 'gold_cluster_id',  'header': 'GoldClusterID',   'format': 's',    'justify': 'L'},
                      {'name': 'system_cluster_id','header': 'SystemClusterID', 'format': 's',    'justify': 'L'},
                      {'name': 'precision',        'header': 'Prec',            'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'recall',           'header': 'Recall',          'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'f1',               'header': 'F1',              'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def get_augmented_types(self, document_id, types):
        region_types = self.get('annotated_regions').get('types_annotated_for_document', document_id)
        augmented_types = get_augmented_types_utility(region_types, types)
        return augmented_types

    def score_responses(self):
        scores = []
        for document_id in self.get('core_documents'):
            # add scores corresponding to all gold clusters
            document = self.get('gold_responses').get('document_mappings').get('documents').get(document_id)
            language = document.get('language')
            self.record_event('ANNOTATED_TYPES_INFO', document_id, ','.join(self.get('annotated_regions').get('types_annotated_for_document', document_id)))
            document_gold_to_system = self.get('cluster_alignment').get('gold_to_system').get(document_id)
            for gold_cluster_id in document_gold_to_system if document_gold_to_system else []:
                system_cluster_id = document_gold_to_system.get(gold_cluster_id).get('aligned_to')
                aligned_similarity = document_gold_to_system.get(gold_cluster_id).get('aligned_similarity')
                precision, recall, f1 = [0,0,0]
                if gold_cluster_id == 'None': continue
                gold_cluster = self.get('gold_responses').get('document_clusters').get(document_id).get(gold_cluster_id)
                metatype = gold_cluster.get('metatype')
                if metatype not in ['Entity', 'Event']: continue
                if system_cluster_id != 'None':
                    if aligned_similarity == 0:
                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')
                    system_cluster = self.get('cluster', 'system', document_id, system_cluster_id)
                    if system_cluster.get('metatype') != metatype:
                        self.record_event('UNEXPECTED_ALIGNED_CLUSTER_METATYPE', system_cluster.get('metatype'), system_cluster_id, metatype, gold_cluster_id)
                    gold_types = set(gold_cluster.get('all_expanded_types'))
                    system_types = set()
                    if document_id in self.get('system_responses').get('document_clusters'):
                        system_types = set(self.get('system_responses').get('document_clusters').get(document_id).get(system_cluster_id).get('all_expanded_types'))
                    augmented_gold_types = self.get('augmented_types', document_id, gold_types)
                    augmented_system_types = self.get('augmented_types', document_id, system_types)
                    self.record_event('TYPE_METRIC_SCORE_INFO', self.__class__.__name__, 'TYPES_SUBMITTED', document_id, gold_cluster_id, ','.join(gold_types), system_cluster_id, ','.join(system_types))
                    self.record_event('TYPE_METRIC_SCORE_INFO', self.__class__.__name__, 'TYPES_SCORED', document_id, gold_cluster_id, ','.join(augmented_gold_types), system_cluster_id, ','.join(augmented_system_types))
                    precision, recall, f1 = get_precision_recall_and_f1(augmented_gold_types, augmented_system_types)
                score = TypeMetricScoreV1(logger=self.logger,
                                          run_id=self.get('run_id'),
                                          document_id=document_id,
                                          language=language,
                                          metatype=metatype,
                                          gold_cluster_id=gold_cluster_id,
                                          system_cluster_id=system_cluster_id,
                                          precision=precision,
                                          recall=recall,
                                          f1=f1)
                scores.append(score)
            # add scores unaligned system clusters
            document_system_to_gold = self.get('cluster_alignment').get('system_to_gold').get(document_id)
            for system_cluster_id in document_system_to_gold if document_system_to_gold else []:
                gold_cluster_id = document_system_to_gold.get(system_cluster_id).get('aligned_to')
                aligned_similarity = document_system_to_gold.get(system_cluster_id).get('aligned_similarity')
                if system_cluster_id != 'None':
                    system_cluster = self.get('system_responses').get('document_clusters').get(document_id).get(system_cluster_id)
                    metatype = system_cluster.get('metatype')
                    if metatype not in ['Entity', 'Event']: continue
                    if gold_cluster_id == 'None':
                        precision, recall, f1 = [0,0,0]
                        score = TypeMetricScoreV1(logger=self.logger,
                                                  run_id=self.get('run_id'),
                                                  document_id=document_id,
                                                  language=language,
                                                  metatype=metatype,
                                                  gold_cluster_id=gold_cluster_id,
                                                  system_cluster_id=system_cluster_id,
                                                  precision=precision,
                                                  recall=recall,
                                                  f1=f1)
                        scores.append(score)
                    elif aligned_similarity == 0:
                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')

        scores_printer = ScorePrinter(self.logger, self.printing_specs)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype', False),
                                        ('gold_cluster_id', False),
                                        ('system_cluster_id', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, TypeMetricScoreV1)
        self.scores = scores_printer