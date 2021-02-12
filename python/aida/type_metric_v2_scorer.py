"""
AIDA class for type metric scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.type_metric_v23_score import TypeMetricScoreV23
from aida.utility import get_augmented_type, multisort

class TypeMetricScorerV2(Scorer):
    """
    AIDA class for class query scores.
    """
    
    printing_specs = [{'name': 'document_id',      'header': 'DocID',           'format': 's',    'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',           'format': 's',    'justify': 'L'},
                      {'name': 'language',         'header': 'Language',        'format': 's',    'justify': 'L'},
                      {'name': 'metatype',         'header': 'Metatype',        'format': 's',    'justify': 'L'},
                      {'name': 'gold_cluster_id',  'header': 'GoldClusterID',   'format': 's',    'justify': 'L'},
                      {'name': 'system_cluster_id','header': 'SystemClusterID', 'format': 's',    'justify': 'L'},
                      {'name': 'average_precision','header': 'AvgPrec',         'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, separator=None, **kwargs):
        super().__init__(logger, separator=separator, **kwargs)

    def order(self, k):
        language, metatype = k.split(':')
        metatype = '_ALL' if metatype == 'ALL' else metatype
        language = '_ALL' if language == 'ALL' else language
        return '{language}:{metatype}'.format(metatype=metatype, language=language)

    def get_average_precision(self, document_id, gold_cluster_id, augmented_gold_types, system_cluster_id, augmented_system_types):
        entity_types = {'gold': augmented_gold_types, 'system': augmented_system_types}
        type_weights = list()
        for entity_type in entity_types.get('system'):
            type_weight = {
                'type': entity_type,
                'weight': self.get('type_weight', entity_types.get('system').get(entity_type))
                }
            type_weights.append(type_weight)

        rank = 0
        num_correct = 0
        sum_precision = 0.0
        for type_weight in multisort(type_weights, (('weight', True),
                                                    ('type', False))):
            rank += 1
            label = 'WRONG'
            if type_weight.get('type') in entity_types.get('gold'):
                label = 'RIGHT'
                num_correct += self.get('relevance_weight', type_weight.get('weight'))
                sum_precision += (num_correct/rank)
            self.record_event('TYPE_METRIC_AP_RANKED_LIST', self.__class__.__name__, document_id, gold_cluster_id, system_cluster_id, rank, type_weight.get('type'), label, type_weight.get('weight'), num_correct, sum_precision)

        average_precision = sum_precision/len(entity_types.get('gold')) if len(entity_types.get('gold')) else 0
        return average_precision

    def get_augmented_types(self, document_id, types):
        augmented_types = {}
        region_types = self.get('annotated_regions').get('types_annotated_for_document', document_id)
        for cluster_type in types:
            augmented_type = get_augmented_type(region_types, cluster_type)
            if augmented_type:
                if augmented_type not in augmented_types:
                    augmented_types[augmented_type] = []
                for entry in types.get(cluster_type):
                    augmented_types.get(augmented_type).append(entry)
        return augmented_types

    def get_relevance_weight(self, type_weight):
        return 1

    def get_type_weight(self, entries):
        mentions = {}
        for entry in entries:
            mentions[entry.get('mention_span_text')] = 1
        return len(mentions)

    def score_responses(self):
        scores = []
        mean_average_precisions = {}
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
                average_precision = 0
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
                    gold_types = gold_cluster.get('all_expanded_types')
                    system_types = {}
                    if document_id in self.get('system_responses').get('document_clusters'):
                        system_types = self.get('system_responses').get('document_clusters').get(document_id).get(system_cluster_id).get('all_expanded_types')
                    augmented_gold_types = self.get('augmented_types', document_id, gold_types)
                    augmented_system_types = self.get('augmented_types', document_id, system_types)
                    self.record_event('TYPE_METRIC_SCORE_INFO', 'TYPES_SUBMITTED', document_id, gold_cluster_id, ','.join(gold_types), system_cluster_id, ','.join(system_types))
                    self.record_event('TYPE_METRIC_SCORE_INFO', 'TYPES_SCORED', document_id, gold_cluster_id, ','.join(augmented_gold_types), system_cluster_id, ','.join(augmented_system_types))
                    average_precision = self.get('average_precision', document_id, gold_cluster_id, augmented_gold_types, system_cluster_id, augmented_system_types)
                for metatype_key in ['ALL', metatype]:
                    for language_key in ['ALL', language]:
                        key = '{language}:{metatype}'.format(metatype=metatype_key, language=language_key)
                        mean_average_precisions[key] = mean_average_precisions.get(key, 0) + average_precision
                        counts[key] = counts.get(key, 0) + 1
                score = TypeMetricScoreV23(self.logger,
                                        self.get('run_id'),
                                        document_id,
                                        language,
                                        metatype,
                                        gold_cluster_id,
                                        system_cluster_id,
                                        average_precision)
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
                        average_precision = 0
                        for metatype_key in ['ALL', metatype]:
                            for language_key in ['ALL', language]:
                                key = '{language}:{metatype}'.format(metatype=metatype_key, language=language_key)
                                mean_average_precisions[key] = mean_average_precisions.get(key, 0) + average_precision
                                counts[key] = counts.get(key, 0) + 1
                        score = TypeMetricScoreV23(self.logger,
                                                self.get('run_id'),
                                                document_id,
                                                language,
                                                metatype,
                                                gold_cluster_id,
                                                system_cluster_id,
                                                average_precision)
                        scores.append(score)
                    elif aligned_similarity == 0:
                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')
        scores_printer = ScorePrinter(self.logger, self.printing_specs, self.separator)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype', False),
                                        ('gold_cluster_id', False),
                                        ('system_cluster_id', False))):
            scores_printer.add(score)
        for key in sorted(mean_average_precisions, key=self.order):
            mean_average_precision = mean_average_precisions[key] / counts[key] if counts[key] else 0
            language, metatype = key.split(':')
            mean_score = TypeMetricScoreV23(self.logger,
                                       self.get('run_id'),
                                       'Summary',
                                       language,
                                       metatype,
                                       '',
                                       '',
                                       mean_average_precision,
                                       summary = True)
            scores_printer.add(mean_score)
        self.scores = scores_printer