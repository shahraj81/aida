"""
AIDA class for Argument Extraction evaluation metric scorer.

V2 refers to the variant where we take into account the correctness of the argument assertion justification.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "18 August 2020"

from aida.argument_metric_v1_scorer import ArgumentMetricScorerV1
from aida.utility import get_intersection_over_union, augment_mention_object, spanstring_to_object

class ArgumentMetricScorerV2(ArgumentMetricScorerV1):
    """
    AIDA class for Argument Extraction evaluation metric scorer.

    V2 refers to the variant where we take into account the correctness of the argument assertion justification.
    """

    def __init__(self, logger, separator=None, **kwargs):
        super().__init__(logger, separator=separator, **kwargs)

    def is_predicate_justification_correct(self, system_predicate_justifications, gold_predicate_justifications):
        document_mappings = self.get('gold_responses').get('document_mappings')
        document_boundaries = self.get('gold_responses').get('document_boundaries')
        justification_correctness = False
        max_num_justifications = 2
        for system_predicate_justification in sorted(system_predicate_justifications.values(), key=lambda pj: pj.get('predicate_justification_confidence'), reverse=True):
            system_predicate_justification_span = system_predicate_justification.get('predicate_justification')
            system_mention_object = augment_mention_object(spanstring_to_object(self.logger, system_predicate_justification_span), document_mappings, document_boundaries)
            for gold_predicate_justification in gold_predicate_justifications.values():
                gold_predicate_justification_span = gold_predicate_justification.get('predicate_justification')
                gold_mention_object = augment_mention_object(spanstring_to_object(self.logger, gold_predicate_justification_span), document_mappings, document_boundaries)
                if get_intersection_over_union(system_mention_object, gold_mention_object) > 0:
                    justification_correctness = True
            max_num_justifications -= 1
            if max_num_justifications == 0: break
        return justification_correctness