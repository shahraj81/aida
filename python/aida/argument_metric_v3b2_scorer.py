"""
AIDA class for Argument Extraction evaluation metric scorer V3B2.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 September 2022"

from aida.argument_metric_v3b_scorer import ArgumentMetricScorerV3B

class ArgumentMetricScorerV3B2(ArgumentMetricScorerV3B):
    """
    AIDA class for Argument Metric scorer V3B2.
    
    V3B2 refers to the variant where TRF triples from evaluable system argument assertions that are negated are compared against TRF triples from gold argument assertions that are negated 
    such that argument assertion justification correctness is ignored.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def is_predicate_justification_correct(self, system_predicate_justifications, gold_predicate_justifications):
        return True
