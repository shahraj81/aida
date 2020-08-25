"""
AIDA class for Event/Relation frame evaluation metric scorer.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.frame_metric_score import FrameMetricScore
from aida.utility import get_precision_recall_and_f1

class FrameMetricScorer(Scorer):
    """
    AIDA class for Event/Relation frame evaluation metric scorer.
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
            document_system_to_gold = self.get('cluster_alignment').get('system_to_gold').get(document_id)
            for gold_cluster_id in document_gold_to_system if document_gold_to_system else []:
                system_cluster_id = document_gold_to_system.get(gold_cluster_id).get('aligned_to')
                aligned_similarity = document_gold_to_system.get(gold_cluster_id).get('aligned_similarity')
                precision, recall, f1 = [0,0,0]
                if gold_cluster_id == 'None': continue
                gold_cluster = self.get('gold_responses').get('document_clusters').get(document_id).get(gold_cluster_id)
                if gold_cluster.get('metatype') not in ['Event', 'Relation']: continue
                if system_cluster_id != 'None':
                    if aligned_similarity == 0:
                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')
                    system_cluster = self.get('system_responses').get('document_clusters').get(document_id).get(system_cluster_id)
                    if system_cluster.get('metatype') not in ['Event', 'Relation']: continue
                    gold_frame = self.get('gold_responses').get('document_frames').get(document_id).get(gold_cluster_id)
                    gold_slot_fillers = {}
                    if gold_frame is None:
                        self.record_event('MISSING_GOLD_FRAME', gold_cluster.get('metatype'), gold_cluster_id, document_id, self.get('code_location'))
                        continue
                    for role_name in gold_frame.get('role_fillers'):
                        for gold_filler_cluster_id in gold_frame.get('role_fillers').get(role_name):
                            gold_slot_fillers['{}:{}'.format(role_name, gold_filler_cluster_id)] = 1
                    system_frame = self.get('system_responses').get('document_frames').get(document_id).get(system_cluster_id)
                    system_slot_fillers = {}
                    for role_name in system_frame.get('role_fillers'):
                        for system_filler_cluster_id in system_frame.get('role_fillers').get(role_name):
                            aligned_gold_filler_cluster_id = document_system_to_gold.get(system_filler_cluster_id).get('aligned_to')
                            aligned_gold_filler_cluster_id_similarity = document_system_to_gold.get(system_filler_cluster_id).get('aligned_similarity')
                            if aligned_gold_filler_cluster_id != 'None':
                                if aligned_gold_filler_cluster_id_similarity == 0:
                                    self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')
                                system_slot_fillers['{}:{}'.format(role_name, aligned_gold_filler_cluster_id)] = 1
                            else:
                                system_slot_fillers['{}:{}'.format(role_name, system_filler_cluster_id)] = 1
                    if len(gold_slot_fillers) and len(system_slot_fillers):
                        precision, recall, f1 = get_precision_recall_and_f1(set(gold_slot_fillers.keys()), set(system_slot_fillers.keys()))
                mean_f1 += f1
                count += 1
                score = FrameMetricScore(self.logger, self.get('runid'), document_id,
                                         gold_cluster_id, system_cluster_id,
                                         precision, recall, f1)
                scores.add(score)
            # add scores corresponding to unaligned system clusters
            precision, recall, f1 = [0,0,0]
            for system_cluster_id in document_system_to_gold if document_system_to_gold else []:
                gold_cluster_id = document_system_to_gold.get(system_cluster_id).get('aligned_to')
                aligned_similarity = document_system_to_gold.get(system_cluster_id).get('aligned_similarity')
                if system_cluster_id != 'None':
                    if gold_cluster_id == 'None':
                        count += 1
                        score = FrameMetricScore(self.logger, self.get('runid'), document_id,
                                                 gold_cluster_id, system_cluster_id,
                                                 precision, recall, f1)
                        scores.add(score)
                    elif aligned_similarity == 0:
                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')

        mean_f1 = mean_f1 / count if count else 0
        mean_score = FrameMetricScore(self.logger, self.get('runid'), 'Summary', '', '', '', '', mean_f1, summary = True)
        scores.add(mean_score)
        self.scores = scores