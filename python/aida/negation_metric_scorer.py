"""
Class for negation metric scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.negation_metric_score import NegationMetricScore
from aida.utility import multisort



import random


class NegationMetricScorer(Scorer):
    """
    Class for negation metric scores.
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

    def get_mention_negation_score(self, document_id, system_cluster, system_mention_id, gold_cluster, gold_mention_id):
        system_cluster_id = system_cluster.get('ID')
        mention_negation_score = 0
        if self.get('mention_alignment').get(document_id).get(system_cluster_id).get(system_mention_id):
            gold_mention_id = self.get('mention_alignment').get(document_id).get(system_cluster_id).get(system_mention_id).get('aligned_to')
            system_mention = system_cluster.get('mentions').get(system_mention_id)
            gold_mention = gold_cluster.get('mentions').get(gold_mention_id)
            if system_mention.get('is_negated') == gold_mention.get('is_negated'):
                mention_negation_score = 1.0
        return mention_negation_score

    def score_responses(self):
        scores = []
        for document_id in self.get('core_documents'):
            # add scores corresponding to all gold clusters
            document = self.get('gold_responses').get('document_mappings').get('documents').get(document_id)
            # skip those core documents that do not have an entry in the parent-children table
            if document is None: continue
            language = document.get('language')

            document_system_to_gold = self.get('cluster_alignment').get('system_to_gold').get(document_id)
            for system_cluster_id in document_system_to_gold if document_system_to_gold else []:
                gold_cluster_id = document_system_to_gold.get(system_cluster_id).get('aligned_to')
                if 'None' in [system_cluster_id, gold_cluster_id]: continue
                gold_cluster = self.get('gold_responses').get('document_clusters').get(document_id).get(gold_cluster_id)
                metatype = gold_cluster.get('metatype')
                if metatype not in ['Relation', 'Event']: continue
                gold_mention_ids = list(gold_cluster.get('mentions').keys())
                system_cluster = self.get('system_responses').get('document_clusters').get(document_id).get(system_cluster_id)
                system_mention_ids = list(system_cluster.get('mentions').keys())
                total_mention_negation_score = 0
                for system_mention_id in system_mention_ids:
                    system_mention_alignment = self.get('mention_alignment').get(document_id).get(system_cluster_id).get(system_mention_id)
                    if system_mention_alignment is None: continue
                    gold_mention_id = system_mention_alignment.get('aligned_to')
                    mention_negation_score = self.get('mention_negation_score', document_id, system_cluster, system_mention_id, gold_cluster, gold_mention_id)
                    total_mention_negation_score += mention_negation_score
                precision = total_mention_negation_score / len(system_mention_ids) if len(system_mention_ids) else 0
                recall = total_mention_negation_score / len(gold_mention_ids) if len(gold_mention_ids) else 0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

                score = NegationMetricScore(logger=self.logger,
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

        scores_printer = ScorePrinter(self.logger, self.printing_specs)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype', False),
                                        ('gold_cluster_id', False),
                                        ('system_cluster_id', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, NegationMetricScore)
        self.scores = scores_printer