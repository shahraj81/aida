"""
AIDA class for across documents coreference metric scorer.

Phase3-V2 refers to the variant where num of clusters that can be aligned is equal to number of ECs.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 June 2022"

from aida.across_documents_correference_metric_scorer import AcrossDocumentsCoreferenceMetricScorer

class AcrossDocumentsCoreferenceMetricScorerV2(AcrossDocumentsCoreferenceMetricScorer):
    """
    AIDA class for across documents coreference metric scorer.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def get_num_clusters(self, query_id):
        return int(len(self.get('equivalence_classes', query_id)))
