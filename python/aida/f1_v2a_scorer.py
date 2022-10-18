"""
AIDA class for Task3 F1 scorer (Variant 2A) is the same as that of Variant 2 but was created for naming consistency.

V2A refers to the variant where:
  - claims considered for scoring are limited to the pooling depth.
  - required fields include: claimTemplate, claimEpistemic, xVariable, claimer
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 June 2022"

from aida.f1_v2_scorer import F1ScorerV2

class F1ScorerV2A(F1ScorerV2):
    """
    AIDA class for Task3 F1 scorer V2A.
    
    V2A refers to the variant where:
      - claims considered for scoring are limited to the pooling depth.
      - required fields include: claimTemplate, claimEpistemic, xVariable, claimer
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)