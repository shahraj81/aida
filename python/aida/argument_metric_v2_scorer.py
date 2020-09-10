"""
AIDA class for Argument Extraction evaluation metric scorer.

V2 refers to the variant where we take into account the correctness of the argument assertion justification.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.score_printer import ScorePrinter
from aida.scorer import Scorer
from aida.argument_metric_score import ArgumentMetricScore
from aida.utility import get_precision_recall_and_f1, spanstring_to_object, get_intersection_over_union, augment_mention_object, trim_cv, multisort

class ArgumentMetricScorerV2(Scorer):
    """
    AIDA class for Argument Extraction evaluation metric scorer.

    V2 refers to the variant where we take into account the correctness of the argument assertion justification.
    """
    
    printing_specs = [{'name': 'document_id',      'header': 'DocID',           'format': 's',    'justify': 'L'},
                      {'name': 'run_id',           'header': 'RunID',           'format': 's',    'justify': 'L'},
                      {'name': 'language',         'header': 'Language',        'format': 's',    'justify': 'L'},
                      {'name': 'metatype',         'header': 'Metatype',        'format': 's',    'justify': 'L'},
                      {'name': 'precision',        'header': 'Prec',            'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'recall',           'header': 'Recall',          'format': '6.4f', 'justify': 'R', 'mean_format': 's'},
                      {'name': 'f1',               'header': 'F1',              'format': '6.4f', 'justify': 'R', 'mean_format': '6.4f'}]

    def __init__(self, logger, annotated_regions, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator=None):
        super().__init__(logger, annotated_regions, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, separator)

    def is_valid_slot(self, slot_name):
        if slot_name in self.get('gold_responses').get('slot_mappings').get('mappings').get('type_to_codes'):
            return True
        return False

    def order(self, k):
        language, metatype = k.split(':')
        metatype = '_ALL' if metatype == 'ALL' else metatype
        language = '_ALL' if language == 'ALL' else language
        return '{language}:{metatype}'.format(metatype=metatype, language=language)

    def score_responses(self):
        scores = []
        mean_f1s = {}
        counts = {}
        for document_id in self.get('core_documents'):
            language = self.get('gold_responses').get('document_mappings').get('documents').get(document_id).get('language')
            gold_trfs = {}
            if document_id in self.get('gold_responses').get('document_frames'):
                for gold_frame in self.get('gold_responses').get('document_frames').get(document_id).values():
                    metatype = gold_frame.get('metatype')
                    for role_name in gold_frame.get('role_fillers'):
                        for filler_cluster_id in gold_frame.get('role_fillers').get(role_name):
                            for predicate_justification in gold_frame.get('role_fillers').get(role_name).get(filler_cluster_id):
                                type_invoked = predicate_justification.get('predicate').split('_')[0]
                                type_invoked_elements = type_invoked.split('.')
                                if len(type_invoked_elements) == 3:
                                    type_invoked_elements.pop()
                                    parent_type_invoked = '.'.join(type_invoked_elements)
                                    parent_predicate = '{parent_type_invoked}_{role_name}'.format(parent_type_invoked=parent_type_invoked,
                                                                                                  role_name=role_name)
                                    if self.is_valid_slot(parent_predicate):
                                        type_invoked = parent_type_invoked
                                trf = '{type_invoked}_{role_name}:{filler_cluster_id}'.format(type_invoked=type_invoked,
                                                                                          role_name=role_name,
                                                                                          filler_cluster_id=filler_cluster_id)

                                for metatype_key in ['ALL', metatype]:
                                    key = '{language}:{metatype}'.format(language=language, metatype=metatype_key)
                                    if key not in gold_trfs:
                                        gold_trfs[key] = {}
                                    if trf not in gold_trfs[key]:
                                        gold_trfs[key][trf] = {}

                                    predicate_justification_span = predicate_justification.get('predicate_justification')
                                    predicate_justification_confidence = trim_cv(predicate_justification.get('argument_assertion_confidence'))
                                    predicate_justification_confidence *= trim_cv(predicate_justification.get('predicate_justification_confidence'))
                                    gold_trfs[key][trf][predicate_justification_span] = predicate_justification_confidence

            system_trfs = {}
            candidate_system_trfs = {}
            if document_id in self.get('system_responses').get('document_frames'):
                document_system_to_gold = self.get('cluster_alignment').get('system_to_gold').get(document_id)
                for system_frame in self.get('system_responses').get('document_frames').get(document_id).values():
                    metatype = system_frame.get('metatype')
                    for role_name in system_frame.get('role_fillers'):
                        for filler_cluster_id in system_frame.get('role_fillers').get(role_name):
                            for predicate_justification in system_frame.get('role_fillers').get(role_name).get(filler_cluster_id):
                                type_invoked = predicate_justification.get('predicate').split('_')[0]
                                type_invoked_elements = type_invoked.split('.')
                                if len(type_invoked_elements) == 3:
                                    type_invoked_elements.pop()
                                    parent_type_invoked = '.'.join(type_invoked_elements)
                                    parent_predicate = '{parent_type_invoked}_{role_name}'.format(parent_type_invoked=parent_type_invoked,
                                                                                                  role_name=role_name)
                                    if self.is_valid_slot(parent_predicate):
                                        type_invoked = parent_type_invoked
                                aligned_gold_filler_cluster_id = document_system_to_gold.get(filler_cluster_id).get('aligned_to')
                                aligned_gold_filler_cluster_id = filler_cluster_id if aligned_gold_filler_cluster_id == 'None' else aligned_gold_filler_cluster_id
                                aligned_gold_filler_cluster_id_similarity = document_system_to_gold.get(filler_cluster_id).get('aligned_similarity')
                                if aligned_gold_filler_cluster_id != 'None':
                                    if aligned_gold_filler_cluster_id_similarity == 0:
                                        self.record_event('DEFAULT_CRITICAL_ERROR', 'aligned_similarity=0')
                                trf = '{type_invoked}_{role_name}:{filler_cluster_id}'.format(type_invoked=type_invoked,
                                                                                          role_name=role_name,
                                                                                          filler_cluster_id=aligned_gold_filler_cluster_id)

                                for metatype_key in ['ALL', metatype]:
                                    key = '{language}:{metatype}'.format(language=language, metatype=metatype_key)
                                    if key not in candidate_system_trfs:
                                        candidate_system_trfs[key] = {}
                                    if trf not in candidate_system_trfs[key]:
                                        candidate_system_trfs[key][trf] = {}
                                    predicate_justification_span = predicate_justification.get('predicate_justification')
                                    predicate_justification_confidence = trim_cv(predicate_justification.get('argument_assertion_confidence'))
                                    predicate_justification_confidence *= trim_cv(predicate_justification.get('predicate_justification_confidence'))
                                    candidate_system_trfs.get(key)[trf][predicate_justification_span] = predicate_justification_confidence

            document_mappings = self.get('gold_responses').get('document_mappings')
            document_boundaries = self.get('gold_responses').get('document_boundaries')
            for key in candidate_system_trfs:
                for trf in candidate_system_trfs[key]:
                    if key not in gold_trfs: continue
                    if trf not in gold_trfs[key]: continue
                    max_num_justifications = 2
                    justification_correctness = False
                    for system_predicate_justification_span in sorted(candidate_system_trfs[key][trf], key=lambda s: candidate_system_trfs[key][trf][s], reverse=True):
                        system_mention_object = augment_mention_object(spanstring_to_object(self.logger, system_predicate_justification_span), document_mappings, document_boundaries)
                        for gold_predicate_justification_span in gold_trfs[key][trf]:
                            gold_mention_object = augment_mention_object(spanstring_to_object(self.logger, gold_predicate_justification_span), document_mappings, document_boundaries)
                            if get_intersection_over_union(system_mention_object, gold_mention_object) > 0:
                                justification_correctness = True
                        max_num_justifications -= 1
                        if max_num_justifications == 0: break
                    if justification_correctness:
                        if key not in system_trfs:
                            system_trfs[key] = {}
                        system_trfs[key][trf] = 1

            for key in set().union(gold_trfs, system_trfs):
                language, metatype = key.split(':')
                gold_trf_set = set(gold_trfs.get(key, dict()).keys())
                system_trf_set = set(system_trfs.get(key, dict()).keys())
                precision, recall, f1 = get_precision_recall_and_f1(gold_trf_set, system_trf_set)
                for language_key in ['ALL', language]:
                    aggregate_key = '{language}:{metatype}'.format(language=language_key, metatype=metatype)
                    mean_f1s[aggregate_key] = mean_f1s.get(aggregate_key, 0) + f1
                    counts[aggregate_key] = counts.get(aggregate_key, 0) + 1
                score = ArgumentMetricScore(self.logger, self.get('runid'), document_id, language, metatype,
                                     precision, recall, f1)
                scores.append(score)

        scores_printer = ScorePrinter(self.logger, self.printing_specs, self.separator)
        for score in multisort(scores, (('document_id', False),
                                        ('metatype_sortkey', False))):
            scores_printer.add(score)

        for key in sorted(mean_f1s, key=self.order):
            mean_f1 = mean_f1s[key] / counts[key] if counts[key] else 0
            language, metatype = key.split(':')
            mean_score = ArgumentMetricScore(self.logger, self.get('runid'), 'Summary', language, metatype, '', '', mean_f1, summary = True)
            scores_printer.add(mean_score)

        self.scores = scores_printer