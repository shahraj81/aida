"""
AIDA class for Argument Extraction evaluation metric scorer V3A2.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 September 2022"

from aida.argument_metric_v3a_scorer import ArgumentMetricScorerV3A

class ArgumentMetricScorerV3A2(ArgumentMetricScorerV3A):
    """
    AIDA class for Argument Metric scorer V3A2.
    
    V3A2 refers to the variant where TRF triples from all evaluable system argument assertions are compared against TRF triples from all gold argument assertions
    such that argument assertion justification correctness is ignored.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def is_predicate_justification_correct(self, system_predicate_justifications, gold_predicate_justifications):
        return True
