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
from aida.utility import get_precision_recall_and_f1, multisort

class FrameMetricScorer(Scorer):
    """
    AIDA class for Event/Relation frame evaluation metric scorer.
    """
    
    printing_specs = [{'name': 'document_id',      'header': 'DocID',           'format': 's',    'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',           'format': 's',    'justify': 'L'},
                      {'name': 'metatype',         'header': 'Metatype',        'format': 's',    'justify': 'L'},
                      {'name': 'gold_cluster_id',  'header': 'GoldClusterID',   'format': 's',    'justify': 'L'},
                      {'name': 'system_cluster_id','header': 'SystemClusterID', 'format': 's',    'justify': 'L'},
                      {'name': 'precision',        'header': 'Prec',            'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'recall',           'header': 'Recall',          'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'f1',               'header': 'F1',              'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, annotated_regions, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator=None):
        super().__init__(logger, annotated_regions, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator)

    def order(self, k):
        m = {'Entity': 1, 'Event': 2, 'Relation': 3, 'ALL': 4}
        return m[k]

    def score_responses(self):
        scores = []
        mean_f1s = {}
        counts = {}
        for document_id in self.get('core_documents'):
            # add scores corresponding to all gold clusters
            document_gold_to_system = self.get('cluster_alignment').get('gold_to_system').get(document_id)
            document_system_to_gold = self.get('cluster_alignment').get('system_to_gold').get(document_id)
            for gold_cluster_id in document_gold_to_system if document_gold_to_system else []:
                system_cluster_id = document_gold_to_system.get(gold_cluster_id).get('aligned_to')
                aligned_similarity = document_gold_to_system.get(gold_cluster_id).get('aligned_similarity')
                precision, recall, f1 = [0,0,0]
                if gold_cluster_id == 'None': continue
                gold_cluster = self.get('cluster', 'gold', document_id, gold_cluster_id)
                metatype = gold_cluster.get('metatype')
                if metatype not in ['Event', 'Relation']: continue
                if system_cluster_id != 'None':
                    if aligned_similarity == 0:
                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')
                    system_cluster = self.get('cluster', 'system', document_id, system_cluster_id)
                    if system_cluster.get('metatype') != metatype:
                        self.record_event('UNEXPECTED_ALIGNED_CLUSTER_METATYPE', system_cluster.get('metatype'), system_cluster_id, metatype, gold_cluster_id)
                    gold_frame = self.get('frame', 'gold', document_id, gold_cluster_id)
                    gold_slot_fillers = {}
                    if gold_frame is None or len(gold_frame.get('role_fillers'))==0:
                        if gold_cluster.get('metatype') == 'Relation':
                            self.record_event('MISSING_GOLD_FRAME', gold_cluster.get('metatype'), gold_cluster_id, document_id, self.get('code_location'))
                        continue
                    for role_name in gold_frame.get('role_fillers'):
                        for gold_filler_cluster_id in gold_frame.get('role_fillers').get(role_name):
                            gold_slot_fillers['{}:{}'.format(role_name, gold_filler_cluster_id)] = 1
                    system_frame = self.get('frame', 'system', document_id, system_cluster_id)
                    if system_frame:
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
                for key in ['ALL', metatype]:
                    mean_f1s[key] = mean_f1s.get(key, 0) + f1
                    counts[key] = counts.get(key, 0) + 1
                score = FrameMetricScore(self.logger, self.get('runid'), document_id, metatype,
                                         gold_cluster_id, system_cluster_id,
                                         precision, recall, f1)
                scores.append(score)
            # add scores corresponding to unaligned system clusters
            precision, recall, f1 = [0,0,0]
            for system_cluster_id in document_system_to_gold if document_system_to_gold else []:
                gold_cluster_id = document_system_to_gold.get(system_cluster_id).get('aligned_to')
                aligned_similarity = document_system_to_gold.get(system_cluster_id).get('aligned_similarity')
                if system_cluster_id != 'None':
                    if gold_cluster_id == 'None':
                        metatype = self.get('cluster', 'system', document_id, system_cluster_id).get('metatype')
                        if metatype not in ['Event', 'Relation']: continue
                        counts['ALL'] = counts.get('ALL',0) + 1
                        counts[metatype] = counts.get(metatype, 0) + 1
                        score = FrameMetricScore(self.logger, self.get('runid'), document_id, metatype,
                                                 gold_cluster_id, system_cluster_id,
                                                 precision, recall, f1)
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
            mean_score = FrameMetricScore(self.logger, self.get('runid'), 'Summary', key, '', '', '', '', mean_f1, summary = True)
            scores_printer.add(mean_score)

        self.scores = scores_printer