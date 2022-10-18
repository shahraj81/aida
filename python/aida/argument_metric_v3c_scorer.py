"""
AIDA class for Argument Extraction evaluation metric scorer.

This class serves as the base class all the sub-variants of the Argument Extraction evaluation metric scorer variant 3C used in Phase 3.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 September 2022"

from aida.argument_metric_v3_scorer import ArgumentMetricScorerV3
from aida.container import Container

class ArgumentMetricScorerV3C(ArgumentMetricScorerV3):
    """
    AIDA class for Argument Metric scorer V3C.
    
    This class serves as the base class all the sub-variants of the Argument Extraction evaluation metric scorer variant 3C used in Phase 3.
    
    V3C refers to the variant where TRF triples from evaluable system argument assertions that are not negated are compared against TRF triples from gold argument assertions that are not negated.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def filter(self, trfs):
        retVal = Container(self.get('logger'))
        for trf_id in trfs:
            trf = trfs.get(trf_id)
            if 'NotNegated' in trf.get('negation_status'):
                retVal.add(trf, key=trf_id)
        return retVal
