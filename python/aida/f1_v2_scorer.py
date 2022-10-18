"""
AIDA class for Task3 F1 scorer (Variant 2).

V2 refers to the variant where:
  - claims considered for scoring are limited to the pooling depth.
  - Required fields include: claimTemplate, claimEpistemic, xVariable, claimer
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 June 2022"

from aida.f1_v1_scorer import F1ScorerV1

class F1ScorerV2(F1ScorerV1):
    """
    AIDA class for Task3 F1 scorer V2.
    
    V2 refers to the variant where:
      - claims considered for scoring are limited to the pooling depth.
      - Required fields include: claimTemplate, claimEpistemic, xVariable, claimer
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def get_ranked_claims(self, query, claim_relation, ranked_list_type):
        if ranked_list_type == 'submitted':
            return self.get('ranked_claims_submitted', query, claim_relation, LIMITED_TO_POOLING_DEPTH=True)
        elif ranked_list_type == 'ideal':
            return self.get('ranked_claims_ideal', query, claim_relation, LIMITED_TO_POOLING_DEPTH=True)