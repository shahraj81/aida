"""
AIDA class for type metric scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.type_metric_score import TypeMetricScore
from aida.utility import get_precision_recall_and_f1, get_augmented_types_utility, multisort

class TypeMetricScorer(Scorer):
    """
    AIDA class for class query scores.
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

    def __init__(self, logger, annotated_regions, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator=None):
        super().__init__(logger, annotated_regions, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator)

    def order(self, k):
        language, metatype = k.split(':')
        metatype = '_ALL' if metatype == 'ALL' else metatype
        language = '_ALL' if language == 'ALL' else language
        return '{language}:{metatype}'.format(metatype=metatype, language=language)

    def get_augmented_types(self, document_id, types):
        region_types = self.get('annotated_regions').get('types_annotated_for_document', document_id)
        augmented_types = get_augmented_types_utility(region_types, types)
        return augmented_types

    def score_responses(self):
        scores = []
        mean_f1s = {}
        counts = {}
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
                    self.record_event('TEMPORAL_METRIC_SCORE_INFO', 'TYPES_SUBMITTED', document_id, gold_cluster_id, ','.join(gold_types), system_cluster_id, ','.join(system_types))
                    self.record_event('TEMPORAL_METRIC_SCORE_INFO', 'TYPES_SCORED', document_id, gold_cluster_id, ','.join(augmented_gold_types), system_cluster_id, ','.join(augmented_system_types))
                    precision, recall, f1 = get_precision_recall_and_f1(augmented_gold_types, augmented_system_types)
                for metatype_key in ['ALL', metatype]:
                    for language_key in ['ALL', language]:
                        key = '{language}:{metatype}'.format(metatype=metatype_key, language=language_key)
                        mean_f1s[key] = mean_f1s.get(key, 0) + f1
                        counts[key] = counts.get(key, 0) + 1
                score = TypeMetricScore(self.logger,
                                        self.get('runid'),
                                        document_id,
                                        language,
                                        metatype,
                                        gold_cluster_id,
                                        system_cluster_id,
                                        precision,
                                        recall,
                                        f1)
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
                        for metatype_key in ['ALL', metatype]:
                            for language_key in ['ALL', language]:
                                key = '{language}:{metatype}'.format(metatype=metatype_key, language=language_key)
                                mean_f1s[key] = mean_f1s.get(key, 0) + f1
                                counts[key] = counts.get(key, 0) + 1
                        score = TypeMetricScore(self.logger,
                                                self.get('runid'),
                                                document_id,
                                                language,
                                                metatype,
                                                gold_cluster_id,
                                                system_cluster_id,
                                                precision,
                                                recall,
                                                f1)
                        scores.append(score)
                    elif aligned_similarity == 0:
                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')

        scores_printer = ScorePrinter(self.logger, self.printing_specs, self.separator)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype', False),
                                        ('gold_cluster_id', False),
                                        ('system_cluster_id', False))):
            scores_printer.add(score)
        for key in sorted(mean_f1s, key=self.order):
            mean_f1 = mean_f1s[key] / counts[key] if counts[key] else 0
            language, metatype = key.split(':')
            mean_score = TypeMetricScore(self.logger,
                                       self.get('runid'),
                                       'Summary',
                                       language,
                                       metatype,
                                       '',
                                       '',
                                       '',
                                       '',
                                       mean_f1,
                                       summary = True)
            scores_printer.add(mean_score)
        self.scores = scores_printer