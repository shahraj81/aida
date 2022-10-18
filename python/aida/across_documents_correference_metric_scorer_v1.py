"""
AIDA class for across documents coreference metric scorer.

Phase3-V1 is the same as AcrossDocumentsCoreferenceMetricScorer but was created for naming consistency.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 June 2022"

from aida.across_documents_correference_metric_scorer import AcrossDocumentsCoreferenceMetricScorer

class AcrossDocumentsCoreferenceMetricScorerV1(AcrossDocumentsCoreferenceMetricScorer):
    """
    AIDA class for across documents coreference metric scorer.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)
