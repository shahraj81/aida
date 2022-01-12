"""
Class for variant # 3 of the type metric scores.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "8 February 2021"

from aida.type_metric_v2_scorer import TypeMetricScorerV2
from aida.utility import trim_cv

class TypeMetricScorerV3(TypeMetricScorerV2):
    """
    Class for variant # 3 of the type metric scores.

    This variant of the scorer ranks the types asserted on the cluster, and computes AP where:
        * ranking is induced using weights on types, and
        * the weight on a type is computed as max over the aggregate confidences on mentions asserting that type.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def get_aggregate_confidence(self, entry):
        field_names = ['type_statement_confidence', 'cluster_membership_confidence', 'mention_type_justification_confidence'] 
        confidence = 1.0
        for field_name in field_names:
            confidence *= trim_cv(entry.get(field_name))
        return confidence

    def get_type_weight(self, entries):
        weight = 0
        for entry in entries:
            aggregate_confidence = self.get('aggregate_confidence', entry)
            if aggregate_confidence > weight:
                weight = aggregate_confidence
        return weight