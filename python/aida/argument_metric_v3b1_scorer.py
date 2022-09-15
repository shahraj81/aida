"""
AIDA class for Argument Extraction evaluation metric scorer V3B1.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 September 2022"

from aida.argument_metric_v3b_scorer import ArgumentMetricScorerV3B
from aida.utility import get_intersection_over_union, augment_mention_object, spanstring_to_object

class ArgumentMetricScorerV3B1(ArgumentMetricScorerV3B):
    """
    AIDA class for Argument Metric scorer V3B1.
    
    V3B1 refers to the variant where TRF triples from evaluable system argument assertions that are negated are compared against TRF triples from gold argument assertions that are negated 
    such that at least one of the system’s top two highest confidence argument assertion must have a correct justification.
    
      - A justification for a system argument assertion is defined to be correct if it overlaps with a justification in the gold standard with IOU >= α (α may vary with modality). For Phases 2 and 3 evaluation, we set IOU > 0.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

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