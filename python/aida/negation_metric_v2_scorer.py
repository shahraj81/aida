"""
Class for negation metric scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.negation_metric_v2_score import NegationMetricScoreV2
from aida.utility import multisort

class NegationMetricScorerV2(Scorer):
    """
    Class for negation metric scores.
    """

    printing_specs = [{'name': 'document_id',      'header': 'DocID',           'format': 's',    'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',           'format': 's',    'justify': 'L'},
                      {'name': 'language',         'header': 'Language',        'format': 's',    'justify': 'L'},
                      {'name': 'metatype',         'header': 'Metatype',        'format': 's',    'justify': 'L'},
                      {'name': 'precision',        'header': 'Prec',            'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'},
                      {'name': 'recall',           'header': 'Recall',          'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'},
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
        metatypes = {
            'ALL': ['Entity', 'Event'],
            'Entity': ['Entity'],
            'Event': ['Event']
            }
        scores = []
        for document_id in self.get('core_documents'):
            document = self.get('gold_responses').get('document_mappings').get('documents').get(document_id)
            # skip those core documents that do not have an entry in the parent-children table
            if document is None: continue
            language = document.get('language')

            responses = {
                'gold': self.get('gold_responses'),
                'system': self.get('system_responses'),
                }

            negated_mention_exists = {}
            for system_or_gold in responses:
                if document_id in responses.get(system_or_gold).get('document_clusters'):
                    for cluster in responses.get(system_or_gold).get('document_clusters').get(document_id).values():
                        for mention in cluster.get('mentions').values():
                            if mention.get('is_negated') == 'Negated':
                                cluster_metatype = cluster.get('metatype')
                                for metatype_key in metatypes:
                                    if cluster_metatype in metatypes.get(metatype_key):
                                        negated_mention_exists[metatype_key] = True

            for metatype_key in metatypes:
                if negated_mention_exists.get(metatype_key): continue
                true_positive, false_positive, false_negative = 0, 0, 0
                document_system_to_gold = self.get('cluster_alignment').get('system_to_gold').get(document_id)
                for system_cluster_id in document_system_to_gold if document_system_to_gold else []:
                    gold_cluster_id = document_system_to_gold.get(system_cluster_id).get('aligned_to')
                    if 'None' in [system_cluster_id, gold_cluster_id]: continue
                    gold_cluster = self.get('gold_responses').get('document_clusters').get(document_id).get(gold_cluster_id)
                    metatype = gold_cluster.get('metatype')
                    if metatype not in metatypes.get(metatype_key): continue
                    if metatype not in ['Relation', 'Event']: continue
                    gold_mention_ids = list(gold_cluster.get('mentions').keys())
                    system_cluster = self.get('system_responses').get('document_clusters').get(document_id).get(system_cluster_id)
                    system_mention_ids = list(system_cluster.get('mentions').keys())
                    for system_mention_id in system_mention_ids:
                        system_cluster_alignment = self.get('mention_alignment').get(document_id).get(system_cluster_id)
                        system_mention_alignment = system_cluster_alignment.get(system_mention_id)
                        if system_mention_alignment is None: continue
                        gold_mention_id = system_mention_alignment.get('aligned_to')
                        if system_cluster_alignment.get('aligned_to') == gold_cluster_id and gold_mention_id in gold_mention_ids:
                            is_system_mention_negated = system_cluster.get('mentions').get(system_mention_id).get('is_negated') == 'Negated'
                            is_gold_mention_negated = gold_cluster.get('mentions').get(gold_mention_id).get('is_negated') == 'Negated'
                            if is_system_mention_negated and is_gold_mention_negated:
                                true_positive += 1
                            elif not is_system_mention_negated and is_gold_mention_negated:
                                false_negative += 1
                            elif is_system_mention_negated and not is_gold_mention_negated:
                                false_positive += 1
                score = NegationMetricScoreV2(logger=self.logger,
                                          run_id=self.get('run_id'),
                                          document_id=document_id,
                                          language=language,
                                          metatype=metatype_key,
                                          true_positive=true_positive,
                                          false_positive=false_positive,
                                          false_negative=false_negative)
                scores.append(score)

        scores_printer = ScorePrinter(self.logger, self.printing_specs)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype', False))):
            scores_printer.add(score)
        self.aggregate_scores(scores_printer, NegationMetricScoreV2)
        self.scores = scores_printer