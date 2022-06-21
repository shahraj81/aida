"""
AIDA class for Task3 F1 scorer (Variant 1B).

V1B refers to the variant where:
  - all the submitted claims are considered for scoring regardless of the pooling depth.
  - required fields include: claimTemplate, claimEpistemic, xVariable
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 June 2022"

from aida.f1_v1_scorer import F1ScorerV1

class F1ScorerV1B(F1ScorerV1):
    """
    AIDA class for Task3 F1 scorer V1B.
    
    V1B refers to the variant where:
      - all the submitted claims are considered for scoring regardless of the pooling depth.
      - required fields include: claimTemplate, claimEpistemic, xVariable
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger, **kwargs)

    def get_specs(self):
        return {
            'claimTemplate': {
                'component': False,
                'dependents': ['claimEpistemic', 'xVariable'],
                'fieldname': 'claimTemplate',
                'importance_rank': 1,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'value',
                'required': True,
                'required_for_f1': True,
                'value_fieldnames': 'value:value',
                'weight': 32,
                },
            'claimEpistemic': {
                'component': False,
                'dependents': ['claimTemplate', 'xVariable'],
                'fieldname': 'claimEpistemic',
                'importance_rank': 2,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'polarity',
                'required': True,
                'required_for_f1': True,
                'value_fieldnames': 'polarity:value',
                'weight': 32,
                },
            'xVariable': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic'],
                'fieldname': 'xVariable',
                'importance_rank': 3,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': True,
                'required_for_f1': True,
                'value_fieldnames': 'ec_similarity:correctness',
                'weight': 32,
                },
            'claimer': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable'],
                'fieldname': 'claimer',
                'importance_rank': 4,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': True,
                'required_for_f1': False,
                'value_fieldnames': 'ec_similarity:correctness',
                'weight': 16,
                },
            'claimerAffiliation': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable', 'claimer'],
                'fieldname': 'claimerAffiliation',
                'importance_rank': 5,
                'max_num_of_values': 3,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': False,
                'required_for_f1': False,
                'value_fieldnames': 'ec_similarity:correctness',
                'weight': 4,
                },
            'claimLocation': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable', 'claimer'],
                'fieldname': 'claimLocation',
                'importance_rank': 6,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': False,
                'required_for_f1': False,
                'value_fieldnames': 'ec_similarity:correctness',
                'weight': 1,
                },
            'claimMedium': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable', 'claimer'],
                'fieldname': 'claimMedium',
                'importance_rank': 7,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'overallAssessment',
                'required': False,
                'required_for_f1': False,
                'value_fieldnames': 'ec_similarity:correctness',
                'weight': 1,
                },
            'date': {
                'component': True,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable', 'claimer'],
                'fieldname': 'date',
                'importance_rank': 8,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'range',
                'required': False,
                'required_for_f1': False,
                'value_fieldnames': 'range:value',
                'weight': 1,
                },
            'claimSentiment': {
                'component': False,
                'dependents': ['claimTemplate', 'claimEpistemic', 'xVariable', 'claimer'],
                'fieldname': 'claimSentiment',
                'importance_rank': 9,
                'max_num_of_values': 1,
                'overall_assessment_fieldname': 'value',
                'required': False,
                'required_for_f1': False,
                'value_fieldnames': 'value:value',
                'weight': 0.5,
                },
            }