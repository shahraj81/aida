"""
AIDA class for Task3 F1 scorer (Variant 1A) is the same as that of Variant 1 but was created for naming consistency.

V1A refers to the variant where:
  - all the submitted claims are considered for scoring regardless of the pooling depth.
  - required fields include: claimTemplate, claimEpistemic, xVariable, claimer
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 June 2022"

from aida.f1_v1_scorer import F1ScorerV1

class F1ScorerV1A(F1ScorerV1):
    """
    AIDA class for Task3 F1 scorer V1A.
    
    V1A refers to the variant where:
      - all the submitted claims are considered for scoring regardless of the pooling depth.
      - required fields include: claimTemplate, claimEpistemic, xVariable, claimer
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)