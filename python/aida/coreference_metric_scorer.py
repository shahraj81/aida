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
from aida.utility import multisort

class CoreferenceMetricScorer(Scorer):
    """
    AIDA class for class query scores.
    """
    
    printing_specs = [{'name': 'document_id',      'header': 'DocID',   'format': 's',    'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',   'format': 's',    'justify': 'L'},
                      {'name': 'language',         'header': 'Language','format': 's',    'justify': 'L'},
                      {'name': 'metatype',         'header': 'Metatype',        'format': 's',    'justify': 'L'},
                      {'name': 'precision',        'header': 'Prec',    'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'recall',           'header': 'Recall',  'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'f1',               'header': 'F1',      'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def get_max_total_similarity(self, document_id, metatypes):
        max_total_similarity = 0
        if document_id in self.get('cluster_alignment').get('gold_to_system'):
            for cluster_id in self.get('cluster_alignment').get('gold_to_system').get(document_id):
                if cluster_id == 'None': continue
                metatype = self.get('metatype', document_id, 'gold', cluster_id)
                if metatype not in metatypes: continue
                max_total_similarity += float(self.get('cluster_alignment').get('gold_to_system').get(document_id).get(cluster_id).get('aligned_similarity'))
        return max_total_similarity

    def get_metatype(self, document_id, system_or_gold, cluster_id):
        responses = {
            'gold': self.get('gold_responses'),
            'system': self.get('system_responses')
            }
        metatype = responses.get(system_or_gold).get('document_clusters').get(document_id).get(cluster_id).get('metatype')
        if metatype not in ['Event', 'Relation', 'Entity']:
            self.record_event('DEFAULT_CRITICAL_ERROR', 'Unknown metatype: {} for {}:{}'.format(metatype, system_or_gold.upper(), cluster_id), self.get('code_location'))
        return metatype

    def get_total_self_similarity(self, system_or_gold, document_id, metatypes):
        total_self_similarity = 0
        if system_or_gold == 'system' and document_id not in self.get('cluster_self_similarities').get(system_or_gold):
            return total_self_similarity
        if document_id in self.get('cluster_self_similarities').get(system_or_gold):
            for cluster_id in self.get('cluster_self_similarities').get(system_or_gold).get(document_id):
                metatype = self.get('metatype', document_id, system_or_gold, cluster_id)
                if metatype not in metatypes: continue
                self_similarity = self.get('cluster_self_similarities').get(system_or_gold).get(document_id).get(cluster_id)
                total_self_similarity += float(self_similarity)
        return total_self_similarity

    def score_responses(self):
        metatypes = {
            'ALL': ['Entity', 'Event'],
            'Entity': ['Entity'],
            'Event': ['Event']
            }
        scores = []
        for document_id in self.get('core_documents'):
            document = self.get('gold_responses').get('document_mappings').get('documents').get(document_id)
            if document is None:
                self.record_event('DEFAULT_WARNING', 'No language information found for document {}'.format(document_id))
                continue
            language = document.get('language')
            for metatype_key in metatypes:
                max_total_similarity = self.get('max_total_similarity', document_id, metatypes[metatype_key])
                total_self_similarity_gold = self.get('total_self_similarity', 'gold', document_id, metatypes[metatype_key])
                total_self_similarity_system = self.get('total_self_similarity', 'system', document_id, metatypes[metatype_key])

                precision = max_total_similarity / total_self_similarity_system if total_self_similarity_system else 0
                recall = max_total_similarity / total_self_similarity_gold if total_self_similarity_gold else 0
                f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
                score = CoreferenceMetricScore(logger=self.logger,
                                               run_id=self.get('run_id'),
                                               document_id=document_id,
                                               language=language,
                                               metatype=metatype_key,
                                               precision=precision,
                                               recall=recall,
                                               f1=f1)
                scores.append(score)

        scores_printer = ScorePrinter(self.logger, self.printing_specs)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype_sortkey', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, CoreferenceMetricScore)
        self.scores = scores_printer