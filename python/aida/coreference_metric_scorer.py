"""
AIDA class for coreference metric scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "17 August 2020"

from aida.scorer import Scorer
from aida.coreference_metric_score import CoreferenceMetricScore
from aida.score_printer import ScorePrinter

class CoreferenceMetricScorer(Scorer):
    """
    AIDA class for class query scores.
    """
    
    printing_specs = [{'name': 'document_id',      'header': 'DocID',   'format': 's', 'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',   'format': 's', 'justify': 'L'},
                      {'name': 'precision',        'header': 'Prec',    'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'recall',           'header': 'Recall',  'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'f1',               'header': 'F1',      'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator=None):
        super().__init__(logger, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator)

    def get_max_total_similarity(self, document_id):
        max_total_similarity = 0
        for cluster_id in self.get('cluster_alignment').get('gold_to_system').get(document_id):
            metatype = self.get('metatype', 'gold', cluster_id)
            if metatype != 'Relation':
                max_total_similarity += float(self.get('cluster_alignment').get('gold_to_system').get(document_id).get(cluster_id).get('aligned_similarity'))
        return max_total_similarity

    def get_metatype(self, system_or_gold, cluster_id):
        metatype = self.get('cluster_self_similarities').get('cluster_to_metatype').get('{}:{}'.format(system_or_gold.upper(), cluster_id))
        if metatype not in ['Event', 'Relation', 'Entity']:
            self.record_event('DEFAULT_CRITICAL_ERROR', 'Unexpected metatype: {} for {}:{}'.format(metatype, system_or_gold.upper(), cluster_id), self.get('code_location'))
        return metatype

    def get_total_self_similarity(self, system_or_gold, document_id):
        total_self_similarity = 0
        if system_or_gold == 'system' and document_id not in self.get('cluster_self_similarities').get(system_or_gold):
            return total_self_similarity
        for cluster_id in self.get('cluster_self_similarities').get(system_or_gold).get(document_id):
            metatype = self.get('metatype', system_or_gold, cluster_id)
            self_similarity = self.get('cluster_self_similarities').get(system_or_gold).get(document_id).get(cluster_id)
            if metatype != 'Relation':
                total_self_similarity += float(self_similarity)
        return total_self_similarity

    def score_responses(self):
        scores = ScorePrinter(self.logger, self.printing_specs, self.separator)
        mean_f1 = 0
        for document_id in self.get('core_documents'):
            max_total_similarity = self.get('max_total_similarity', document_id)
            total_self_similarity_gold = self.get('total_self_similarity', 'gold', document_id)
            total_self_similarity_system = self.get('total_self_similarity', 'system', document_id)

            precision = max_total_similarity / total_self_similarity_system if total_self_similarity_system else 0
            recall = max_total_similarity / total_self_similarity_gold
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
            score = CoreferenceMetricScore(self.logger,
                                   self.get('runid'),
                                   document_id,
                                   precision,
                                   recall,
                                   f1)
            mean_f1 += f1
            scores.add(score)
        mean_f1 = mean_f1 / len(self.get('core_documents').keys())
        mean_score = CoreferenceMetricScore(self.logger,
                                   self.get('runid'),
                                   'Summary',
                                   '',
                                   '',
                                   mean_f1,
                                   summary = True)
        scores.add(mean_score)
        self.scores = scores