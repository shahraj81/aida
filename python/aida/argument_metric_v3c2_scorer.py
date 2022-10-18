"""
AIDA class for Argument Extraction evaluation metric scorer V3C2.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 September 2022"

from aida.argument_metric_v3c_scorer import ArgumentMetricScorerV3C

class ArgumentMetricScorerV3C2(ArgumentMetricScorerV3C):
    """
    AIDA class for Argument Metric scorer V3C2.
        
    V3C2 refers to the variant where TRF triples from evaluable system argument assertions that are not negated are compared against TRF triples from gold argument assertions that are not negated
    such that argument assertion justification correctness is ignored.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def is_predicate_justification_correct(self, system_predicate_justifications, gold_predicate_justifications):
        return True
