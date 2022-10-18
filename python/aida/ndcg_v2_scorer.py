"""
AIDA class for Task3 NDCG scorer V2.

V2 refers to the variant where claims considered for scoring are limited to the pooling depth.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "6 June 2022"

from aida.ndcg_v1_scorer import NDCGScorerV1

class NDCGScorerV2(NDCGScorerV1):
    """
    AIDA class for Task3 NDCG scorer V2.
    
    V2 refers to the variant where claims considered for scoring are limited to the pooling depth.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def get_ranked_claims(self, query, claim_relation, ranked_list_type):
        if ranked_list_type == 'submitted':
            return self.get('ranked_claims_submitted', query, claim_relation, LIMITED_TO_POOLING_DEPTH=True)
        elif ranked_list_type == 'ideal':
            return self.get('ranked_claims_ideal', query, claim_relation, LIMITED_TO_POOLING_DEPTH=True)