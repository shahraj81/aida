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
from aida.utility import get_precision_recall_and_f1

class TypeMetricScorer(Scorer):
    """
    AIDA class for class query scores.
    """
    
    printing_specs = [{'name': 'document_id',      'header': 'DocID',           'format': 's',    'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',           'format': 's',    'justify': 'L'},
                      {'name': 'gold_cluster_id',  'header': 'GoldClusterID',   'format': 's',    'justify': 'L'},
                      {'name': 'system_cluster_id','header': 'SystemClusterID', 'format': 's',    'justify': 'L'},
                      {'name': 'precision',        'header': 'Prec',            'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'recall',           'header': 'Recall',          'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'f1',               'header': 'F1',              'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator=None):
        super().__init__(logger, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator)

    def score_responses(self):
        scores = ScorePrinter(self.logger, self.printing_specs, self.separator)
        mean_f1 = 0
        count = 0
        for document_id in self.get('core_documents'):
            # add scores corresponding to all gold clusters
            document_gold_to_system = self.get('cluster_alignment').get('gold_to_system').get(document_id)
            for gold_cluster_id in document_gold_to_system if document_gold_to_system else []:
                system_cluster_id = document_gold_to_system.get(gold_cluster_id).get('aligned_to')
                aligned_similarity = document_gold_to_system.get(gold_cluster_id).get('aligned_similarity')
                if system_cluster_id and aligned_similarity == 0:
                    self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')
                precision, recall, f1 = [0,0,0]
                if system_cluster_id:
                    gold_cluster_types = set(self.get('gold_responses').get('document_clusters').get(document_id).get(gold_cluster_id).get('all_expanded_types'))
                    system_cluster_types = set(self.get('system_responses').get('document_clusters').get(document_id).get(system_cluster_id).get('all_expanded_types'))
                    precision, recall, f1 = get_precision_recall_and_f1(gold_cluster_types, system_cluster_types)
                mean_f1 += f1
                count += 1
                score = TypeMetricScore(self.logger,
                                        self.get('runid'),
                                        document_id,
                                        gold_cluster_id,
                                        system_cluster_id,
                                        precision,
                                        recall,
                                        f1)
                scores.add(score)
            # add scores unaligned system clusters
            document_system_to_gold = self.get('cluster_alignment').get('system_to_gold').get(document_id)
            for system_cluster_id in document_system_to_gold if document_system_to_gold else []:
                gold_cluster_id = document_system_to_gold.get(system_cluster_id).get('aligned_to')
                aligned_similarity = document_system_to_gold.get(system_cluster_id).get('aligned_similarity')
                if gold_cluster_id and aligned_similarity == 0:
                    self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')
                if gold_cluster_id: continue
                precision, recall, f1 = [0,0,0]
                count += 1
                score = TypeMetricScore(self.logger,
                                        self.get('runid'),
                                        document_id,
                                        gold_cluster_id,
                                        system_cluster_id,
                                        precision,
                                        recall,
                                        f1)
                scores.add(score)

        mean_f1 = mean_f1 / count
        mean_score = TypeMetricScore(self.logger,
                                   self.get('runid'),
                                   'Summary',
                                   '',
                                   '',
                                   '',
                                   '',
                                   mean_f1,
                                   summary = True)
        scores.add(mean_score)
        self.scores = scores