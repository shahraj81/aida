"""
AIDA class for Argument Extraction evaluation metric scorer.

This class serves as the base class all the sub-variants of the Argument Extraction evaluation metric scorer variant 3A used in Phase 3.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 September 2022"

from aida.argument_metric_v3_scorer import ArgumentMetricScorerV3

class ArgumentMetricScorerV3A(ArgumentMetricScorerV3):
    """
    AIDA class for Argument Metric scorer V3A.
    
    This class serves as the base class all the sub-variants of the Argument Extraction evaluation metric scorer variant 3A used in Phase 3.
    
    V3A refers to the variant where TRF triples from all evaluable system argument assertions are compared against TRF triples from all gold argument assertions.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def filter(self, trfs):
        return trfs
