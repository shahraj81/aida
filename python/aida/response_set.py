"""
Set of responses for AIDA.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "22 January 2020"

from aida.claim import Claim
from aida.cluster import Cluster
from aida.container import Container
from aida.file_handler import FileHandler
from aida.file_header import FileHeader
from aida.generator import Generator
from aida.validator import Validator
from aida.normalizer import Normalizer
from aida.event_or_relation_frame import EventOrRelationFrame
from tqdm import tqdm
import os

attributes = {
    'argument_assertion_confidence': {
        'name': 'argument_assertion_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    'claim': {
        'name': 'claim',
        'dependencies': ['claim_uid'],
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_OC_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE'],
        'tasks': ['task3'],
        'generate': 'generate_claim',
        'years': [2021],
        },
    'claim_id': {
        'name': 'claim_id',
        'dependencies': ['kb_claim_id'],
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_OC_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE'],
        'tasks': ['task3'],
        'generate': 'generate_claim_id',
        'validate': 'validate_claim_id',
        'years': [2021],
        },
    'claim_uid': {
        'name': 'claim_uid',
        'dependencies': ['claim_id', 'claim_condition', 'claim_query_topic_or_claim_frame_id'],
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_OC_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE'],
        'tasks': ['task3'],
        'generate': 'generate_claim_uid',
        'validate': 'validate_claim_uid',
        'years': [2021],
        },
    'claim_component_ke': {
        'name': 'claim_component_ke',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE'],
        'tasks': ['task3'],
        'years': [2021],
        },
    'claim_component_key': {
        'name': 'claim_component_key',
        'dependencies': ['claim_id'],
        'generate': 'generate_claim_component_key',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE'],
        'tasks': ['task3'],
        'years': [2021],
        },
    'claim_component_name': {
        'name': 'claim_component_name',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE'],
        'tasks': ['task3'],
        'years': [2021],
        },
    'claim_component_provenance': {
        'name': 'claim_component_provenance',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE'],
        'tasks': ['task3'],
        'years': [2021],
        },
    'claim_component_qnode_id': {
        'name': 'claim_component_qnode_id',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE'],
        'tasks': ['task3'],
        'years': [2021],
        },
    'claim_component_qnode_type': {
        'name': 'claim_component_qnode_type',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE'],
        'tasks': ['task3'],
        'years': [2021],
        },
    'claim_component_qnode_types': {
        'name': 'claim_component_qnode_types',
        'dependencies': ['claim', 'claim_component_key'],
        'generate': 'generate_claim_component_qnode_types',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE'],
        'tasks': ['task3'],
        'years': [2021],
        },
    'claim_component_type': {
        'name': 'claim_component_type',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_claim_component_type',
        'years': [2021],
        },
    'claim_condition': {
        'name': 'claim_condition',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_OC_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task3'],
        'generate': 'generate_claim_condition',
        'validate': 'validate_claim_condition',
        'years': [2021],
        },
    'claim_description': {
        'name': 'claim_description',
        'schemas': ['AIDA_PHASE3_TASK3_OC_RESPONSE'],
        'tasks': ['task3'],
        'years': [2021],
        },
    'claim_epistemic_status': {
        'name': 'claim_epistemic_status',
        'schemas': ['AIDA_PHASE3_TASK3_OC_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_claim_epistemic_status',
        'years': [2021],
        },
    'claim_query_topic_or_claim_frame_id': {
        'name': 'claim_query_topic_or_claim_frame_id',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_OC_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task3'],
        'generate': 'generate_claim_query_topic_or_claim_frame_id',
        'validate': 'validate_claim_query_topic_or_claim_frame_id',
        'years': [2021],
        },
    'claim_relation': {
        'name': 'claim_relation',
        'schemas': ['AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_claim_relation',
        'years': [2021],
        },
    'claim_sentiment_status': {
        'name': 'claim_sentiment_status',
        'schemas': ['AIDA_PHASE3_TASK3_OC_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_claim_sentiment_status',
        'years': [2021],
        },
    'claim_subtopic': {
        'name': 'claim_subtopic',
        'schemas': ['AIDA_PHASE3_TASK3_OC_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_claim_subtopic',
        'years': [2021],
        },
    'claim_template': {
        'name': 'claim_template',
        'schemas': ['AIDA_PHASE3_TASK3_OC_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_claim_template',
        'years': [2021],
        },
    'claim_topic': {
        'name': 'claim_topic',
        'schemas': ['AIDA_PHASE3_TASK3_OC_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_claim_topic',
        'years': [2021],
        },
    'cluster': {
        'dependencies': ['cluster_id', 'document_id'],
        'name': 'cluster',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'generate': 'generate_cluster',
        'years': [2020, 2021],
        },
    'cluster_id': {
        'name': 'cluster_id',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK2_ZH_RESPONSE'],
        'tasks': ['task1', 'task2'],
        'years': [2020, 2021],
        },
    'cluster_membership_confidence': {
        'name': 'cluster_membership_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    'cluster_type': {
        'name': 'cluster_type',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_cluster_type',
        'years': [2020, 2021],
        },
    'date': {
        'dependencies': ['start', 'end', 'subject_cluster'],
        'name': 'date',
        'tasks': ['task1', 'task3'],
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'generate': 'generate_date_start_and_end',
        'validate': 'validate_date_start_and_end',
        'years': [2020, 2021],
        },
    'document_id': {
        'dependencies': ['kb_document_id'],
        'name': 'document_id',
        'tasks': ['task1', 'task2', 'task3'],
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK2_ZH_RESPONSE', 'AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_OC_RESPONSE'],
        'validate': 'validate_document_id',
        'generate': 'generate_document_id',
        'years': [2020, 2021],
        },
    'edge_importance_value': {
        'name': 'edge_importance_value',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_importance_value',
        'years': [2020],
        },
    'end': {
        'dependencies': ['end_after', 'end_before'],
        'name': 'end',
        'tasks': ['task1', 'task3'],
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'generate': 'generate_end',
        'validate': 'validate_date_range',
        'years': [2020, 2021],
        },
    'end_before': {
        'dependencies': ['end_before_month', 'end_before_day', 'end_before_year'],
        'name': 'end_before',
        'tasks': ['task1', 'task3'],
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'generate': 'generate_end_before',
        'validate': 'validate_date',
        'years': [2020, 2021],
        },
    'end_before_day': {
        'name': 'end_before_day',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'end_before_month': {
        'name': 'end_before_month',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'end_before_year': {
        'name': 'end_before_year',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'end_after': {
        'dependencies': ['end_after_month', 'end_after_day', 'end_after_year'],
        'name': 'end_after',
        'tasks': ['task1', 'task3'],
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'generate': 'generate_end_after',
        'validate': 'validate_date',
        'years': [2020, 2021],
        },
    'end_after_day': {
        'name': 'end_after_day',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'end_after_month': {
        'name': 'end_after_month',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'end_after_year': {
        'name': 'end_after_year',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'hypothesis_importance_value': {
        'name': 'hypothesis_importance_value',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_importance_value',
        'years': [2020],
        },
    'is_assertion_negated': {
        'name': 'is_assertion_negated',
        'schemas': ['AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'validate': 'validate_negation_status',
        'years': [2021],
        },
    'is_mention_negated': {
        'name': 'is_mention_negated',
        'schemas': ['AIDA_PHASE3_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_negation_status',
        'years': [2021],
        },
    'is_object_associated_to_claim': {
        'name': 'is_object_associated_to_claim',
        'schemas': ['AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'years': [2020, 2021],
        },
    'is_object_in_claim_semantics': {
        'name': 'is_object_in_claim_semantics',
        'schemas': ['AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'years': [2020, 2021],
        },
    'is_object_cluster_member_negated': {
        'name': 'is_object_cluster_member_negated',
        'schemas': ['AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_negation_status',
        'years': [2021],
        },
    'is_object_prototype_negated': {
        'name': 'is_object_prototype_negated',
        'schemas': ['AIDA_PHASE3_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_negation_status',
        'years': [2021],
        },
    'is_subject_associated_to_claim': {
        'name': 'is_subject_associated_to_claim',
        'schemas': ['AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'years': [2020, 2021],
        },
    'is_subject_in_claim_semantics': {
        'name': 'is_subject_in_claim_semantics',
        'schemas': ['AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'years': [2020, 2021],
        },
    'is_subject_cluster_member_negated': {
        'name': 'is_subject_cluster_member_negated',
        'schemas': ['AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_negation_status',
        'years': [2021],
        },
    'is_subject_prototype_negated': {
        'name': 'is_subject_prototype_negated',
        'schemas': ['AIDA_PHASE3_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_negation_status',
        'years': [2021],
        },
    'justification_confidence': {
        'name': 'justification_confidence',
        'schemas': ['AIDA_PHASE3_TASK2_ZH_RESPONSE'],
        'tasks': ['task2'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    'linking_confidence': {
        'name': 'linking_confidence',
        'schemas': ['AIDA_PHASE3_TASK2_ZH_RESPONSE'],
        'tasks': ['task2'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    'mention_type_justification_confidence': {
        'name': 'mention_type_justification_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    'kb_claim_id': {
        'name': 'kb_claim_id',
        'schemas': ['AIDA_PHASE3_TASK3_CC_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_OC_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task3'],
        'generate': 'generate_kb_claim_id',
        'validate': 'validate_kb_claim_id',
        'years': [2021],
        },
    'kb_document_id': {
        'name': 'kb_document_id',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'generate': 'generate_kb_document_id',
        'validate': 'validate_kb_document_id',
        'years': [2020, 2021],
        },
    'link_target': {
        'name': 'link_target',
        'schemas': ['AIDA_PHASE3_TASK2_ZH_RESPONSE'],
        'tasks': ['task2'],
        'years': [2020, 2021],
        },
    'mention_span_text': {
        'name': 'mention_span_text',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK2_ZH_RESPONSE'],
        'tasks': ['task1', 'task2'],
        'validate': 'validate_value_provenance_triple',
        'years': [2020, 2021],
        },
    'metatype': {
        'name': 'metatype',
        'years': [2020, 2021],
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_metatype',
        },
    'object_cluster': {
        'dependencies': ['object_cluster_id'],
        'generate': 'generate_object_cluster',
        'name': 'object_cluster',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_entries_in_cluster',
        'years': [2020, 2021],
        },
    'object_cluster_handle': {
        'name': 'object_cluster_handle',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'years': [2020, 2021],
        },
    'object_cluster_id': {
        'name': 'object_cluster_id',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'object_cluster_member_id' : {
        'name': 'object_cluster_member_id',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'years': [2020, 2021],
        },
    'object_cluster_member_metatype' : {
        'name': 'object_cluster_member_metatype',
        'schemas': ['AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_metatype',
        'years': [2021],
        },
    'object_cluster_membership_confidence': {
        'name': 'object_cluster_membership_confidence',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    'object_informative_justification_confidence': {
        'name': 'object_informative_justification_confidence',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    'object_informative_justification_span_text': {
        'name': 'object_informative_justification_span_text',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_value_provenance_triple',
        'years': [2020, 2021],
        },
    'object_metatype': {
        'name': 'object_metatype',
        'years': [2021],
        'schemas': ['AIDA_PHASE3_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_metatype',
        },
    'object_type': {
        'name': 'object_type',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_object_type',
        'years': [2020, 2021],
        },
    'predicate': {
        'dependencies': ['subject_cluster'],
        'name': 'predicate',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'validate': 'validate_predicate',
        'years': [2020, 2021],
        },
    'predicate_justification_span_text': {
        'name': 'predicate_justification_span_text',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_value_provenance_triple',
        'years': [2020, 2021],
        },
    'predicate_justification_spans_text': {
        'name': 'predicate_justification_spans_text',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_value_provenance_triples',
        'years': [2020, 2021],
        },
    'predicate_justification_confidence': {
        'name': 'predicate_justification_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    'query_claim_id': {
        'name': 'query_claim_id',
        'schemas': ['AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_query_claim_id',
        'years': [2021],
        },
    'query_claim_uid': {
        'name': 'query_claim_uid',
        'schemas': ['AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE'],
        'tasks': ['task3'],
        'generate': 'generate_query_claim_uid',
        'years': [2021],
        },
    'query_link_target': {
        'name': 'query_link_target',
        'schemas': ['AIDA_PHASE3_TASK2_ZH_RESPONSE'],
        'tasks': ['task2'],
        'years': [2020, 2021],
        },
    'query_topic': {
        'name': 'query_topic',
        'schemas': ['AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_query_topic',
        'years': [2021],
        },
    'rank': {
        'name': 'rank',
        'schemas': ['AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE'],
        'tasks': ['task3'],
        'years': [2021],
        },
    'start': {
        'dependencies': ['start_after', 'start_before'],
        'name': 'start',
        'tasks': ['task1', 'task3'],
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'generate': 'generate_start',
        'validate': 'validate_date_range',
        'years': [2020, 2021],
        },
    'start_before': {
        'dependencies': ['start_before_month', 'start_before_day', 'start_before_year'],
        'name': 'start_before',
        'tasks': ['task1', 'task3'],
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'generate': 'generate_start_before',
        'validate': 'validate_date',
        'years': [2020, 2021],
        },
    'start_before_day': {
        'name': 'start_before_day',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'start_before_month': {
        'name': 'start_before_month',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'start_before_year': {
        'name': 'start_before_year',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'start_after': {
        'dependencies': ['start_after_month', 'start_after_day', 'start_after_year'],
        'name': 'start_after',
        'tasks': ['task1', 'task3'],
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'generate': 'generate_start_after',
        'validate': 'validate_date',
        'years': [2020, 2021],
        },
    'start_after_day': {
        'name': 'start_after_day',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'start_after_month': {
        'name': 'start_after_month',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'start_after_year': {
        'name': 'start_after_year',
        'schemas': ['AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'subject_cluster': {
        'dependencies': ['subject_cluster_id', 'document_id'],
        'generate': 'generate_subject_cluster',
        'name': 'subject_cluster',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_TM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_entries_in_cluster',
        'years': [2020, 2021],
        },
    'subject_cluster_id': {
        'name': 'subject_cluster_id',
        'schemas': ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_CT_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE'],
        'tasks': ['task1', 'task3'],
        'years': [2020, 2021],
        },
    'subject_cluster_importance_value': {
        'name': 'subject_cluster_importance_value',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_importance_value',
        'years': [2020],
        },
    'subject_cluster_member_id' : {
        'name': 'subject_cluster_member_id',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'years': [2020, 2021],
        },
    'subject_cluster_member_metatype' : {
        'name': 'subject_cluster_member_metatype',
        'schemas': ['AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_metatype',
        'years': [2021],
        },
    'subject_cluster_membership_confidence': {
        'name': 'subject_cluster_membership_confidence',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    'subject_informative_justification_confidence': {
        'name': 'subject_informative_justification_confidence',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    'subject_informative_justification_span_text': {
        'name': 'subject_informative_justification_span_text',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_value_provenance_triple',
        'years': [2020, 2021],
        },
    'subject_metatype': {
        'name': 'subject_metatype',
        'years': [2021],
        'schemas': ['AIDA_PHASE3_TASK1_AM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_metatype',
        },
    'subject_type': {
        'name': 'subject_type',
        'schemas': ['AIDA_PHASE2_TASK3_GR_RESPONSE', 'AIDA_PHASE3_TASK3_GR_RESPONSE'],
        'tasks': ['task3'],
        'validate': 'validate_subject_type',
        'years': [2020, 2021],
        },
    'type_statement_confidence': {
        'name': 'type_statement_confidence',
        'schemas': ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE'],
        'tasks': ['task1'],
        'validate': 'validate_confidence',
        'years': [2020, 2021],
        },
    }

schemas = {
    'AIDA_PHASE2_TASK1_AM_RESPONSE': {
        'name': 'AIDA_PHASE2_TASK1_AM_RESPONSE',
        'year': 2020,
        'task': 'task1',
        'header': ['?metatype', '?subject', '?predicate', '?object', '?predicate_justification', '?argument_assertion_confidence', '?predicate_justification_confidence'],
        'columns': [
            'metatype',
            'subject_cluster_id',
            'predicate',
            'object_cluster_id',
            'predicate_justification_span_text',
            'argument_assertion_confidence',
            'predicate_justification_confidence',
            ]
        },
    'AIDA_PHASE2_TASK1_CM_RESPONSE': {
        'name': 'AIDA_PHASE2_TASK1_CM_RESPONSE',
        'year': 2020,
        'task': 'task1',
        'header': ['?cluster', '?metatype', '?type', '?mention_span', '?type_statement_confidence', '?cluster_membership_confidence', '?mention_type_justification_confidence'],
        'columns': [
            'cluster_id',
            'metatype',
            'cluster_type',
            'mention_span_text',
            'type_statement_confidence',
            'cluster_membership_confidence',
            'mention_type_justification_confidence'
            ]
        },
    'AIDA_PHASE3_TASK1_AM_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK1_AM_RESPONSE',
        'year': 2021,
        'task': 'task1',
        'header': ['?is_assertion_negated', '?subject_metatype', '?subject', '?is_subject_negated', '?predicate', '?object_metatype', '?object', '?is_object_negated', '?predicate_justification', '?argument_assertion_confidence', '?predicate_justification_confidence'],
        'columns': [
            'is_assertion_negated',
            'subject_metatype',
            'subject_cluster_id',
            'is_subject_prototype_negated',
            'predicate',
            'object_metatype',
            'object_cluster_id',
            'is_object_prototype_negated',
            'predicate_justification_span_text',
            'argument_assertion_confidence',
            'predicate_justification_confidence',
            ]
        },
    'AIDA_PHASE3_TASK1_CM_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK1_CM_RESPONSE',
        'year': 2021,
        'task': 'task1',
        'header': ['?cluster', '?metatype', '?type', '?mention_span', '?is_negated', '?type_statement_confidence', '?cluster_membership_confidence', '?mention_type_justification_confidence'],
        'columns': [
            'cluster_id',
            'metatype',
            'cluster_type',
            'mention_span_text',
            'is_mention_negated',
            'type_statement_confidence',
            'cluster_membership_confidence',
            'mention_type_justification_confidence'
            ]
        },
    'AIDA_PHASE3_TASK1_TM_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK1_TM_RESPONSE',
        'year': 2021,
        'task': 'task1',
        'header': ['?cluster', '?sa_month', '?sa_day', '?sa_year', '?sb_month', '?sb_day', '?sb_year', '?ea_month', '?ea_day', '?ea_year', '?eb_month', '?eb_day', '?eb_year'],
        'columns': [
            'subject_cluster_id',
            'start_after_month',
            'start_after_day',
            'start_after_year',
            'start_before_month',
            'start_before_day',
            'start_before_year',
            'end_after_month',
            'end_after_day',
            'end_after_year',
            'end_before_month',
            'end_before_day',
            'end_before_year'
            ]
        },
    'AIDA_PHASE3_TASK2_ZH_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK2_ZH_RESPONSE',
        'year': 2021,
        'task': 'task2',
        'header': ['?docid', '?query_link_target', '?link_target', '?cluster', '?mention_span', '?j_cv', '?link_cv'],
        'columns': [
            'document_id',
            'query_link_target',
            'link_target',
            'cluster_id',
            'mention_span_text',
            'justification_confidence',
            'linking_confidence'
            ]
        },
    'AIDA_PHASE2_TASK3_GR_RESPONSE': {
        'name': 'AIDA_PHASE2_TASK3_GR_RESPONSE',
        'year': 2020,
        'task': 'task3',
        'header': ['?docid', '?edge_type', '?object_cluster', '?objectmo', '?oinf_j_span', '?object_type', 
                   '?subject_cluster', '?subjectmo', '?sinf_j_span', '?subject_type', '?ej_span',
                   '?hypothesis_iv', '?subjectc_iv', '?edge_iv', '?objectc_handle', '?edge_cj_cv', '?oinf_j_cv',
                   '?obcm_cv', '?sinf_j_cv', '?sbcm_cv'],
        'columns': [
            'document_id',
            'predicate',
            'object_cluster_id',
            'object_cluster_member_id',
            'object_informative_justification_span_text',
            'object_type',
            'subject_cluster_id',
            'subject_cluster_member_id',
            'subject_informative_justification_span_text',
            'subject_type',
            'predicate_justification_spans_text',
            'hypothesis_importance_value',
            'subject_cluster_importance_value',
            'edge_importance_value',
            'object_cluster_handle',
            'predicate_justification_confidence',
            'object_informative_justification_confidence',
            'object_cluster_membership_confidence',
            'subject_informative_justification_confidence',
            'subject_cluster_membership_confidence'
            ]
        },
    'AIDA_PHASE3_TASK3_CC_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK3_CC_RESPONSE',
        'year': 2021,
        'task': 'task3',
        'header': ['?claim_id', '?component_type', '?name', '?qnode_id', '?qnode_type', '?provenance', '?ke'],
        'columns': [
            'claim_id',
            'claim_component_type',
            'claim_component_name',
            'claim_component_qnode_id',
            'claim_component_qnode_type',
            'claim_component_provenance',
            'claim_component_ke',
            ]
        },
    'AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE',
        'year': 2021,
        'task': 'task3',
        'header': ['?query_claim_id', '?claim_id', '?rank', '?claim_relation'],
        'columns': [
            'query_claim_id',
            'claim_id',
            'rank',
            'claim_relation',
            ]
        },
    'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE',
        'year': 2021,
        'task': 'task3',
        'header': ['?query_topic', '?claim_id', '?rank'],
        'columns': [
            'query_topic',
            'claim_id',
            'rank',
            ]
        },
    'AIDA_PHASE3_TASK3_CT_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK3_CT_RESPONSE',
        'year': 2021,
        'task': 'task3',
        'header': ['?claim_id', '?sa_month', '?sa_day', '?sa_year', '?sb_month', '?sb_day', '?sb_year', '?ea_month', '?ea_day', '?ea_year', '?eb_month', '?eb_day', '?eb_year'],
        'columns': [
            'claim_id',
            'start_after_month',
            'start_after_day',
            'start_after_year',
            'start_before_month',
            'start_before_day',
            'start_before_year',
            'end_after_month',
            'end_after_day',
            'end_after_year',
            'end_before_month',
            'end_before_day',
            'end_before_year'
            ]
        },
    'AIDA_PHASE3_TASK3_GR_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK3_GR_RESPONSE',
        'year': 2021,
        'task': 'task3',
        'header': ['?docid', '?edge_type', '?is_assertion_negated',
                   '?object_cluster', '?is_object_associated_to_claim', '?is_object_in_claim_semantics',
                   '?objectmo', '?objectmo_metatype', '?is_objectmo_negated', '?oinf_j_span', '?object_type',
                   '?subject_cluster', '?is_subject_associated_to_claim', '?is_subject_in_claim_semantics',
                   '?subjectmo', '?subjectmo_metatype', '?is_subjectmo_negated', '?sinf_j_span', '?subject_type',
                   '?ej_span', '?objectc_handle', '?edge_cj_cv', '?oinf_j_cv', '?obcm_cv', '?sinf_j_cv', '?sbcm_cv'],
        'columns': [
            'document_id',
            'predicate',
            'is_assertion_negated',
            'object_cluster_id',
            'is_object_associated_to_claim',
            'is_object_in_claim_semantics',
            'object_cluster_member_id',
            'object_cluster_member_metatype',
            'is_object_cluster_member_negated',
            'object_informative_justification_span_text',
            'object_type',
            'subject_cluster_id',
            'is_subject_associated_to_claim',
            'is_subject_in_claim_semantics',
            'subject_cluster_member_id',
            'subject_cluster_member_metatype',
            'is_subject_cluster_member_negated',
            'subject_informative_justification_span_text',
            'subject_type',
            'predicate_justification_spans_text',
            'object_cluster_handle',
            'predicate_justification_confidence',
            'object_informative_justification_confidence',
            'object_cluster_membership_confidence',
            'subject_informative_justification_confidence',
            'subject_cluster_membership_confidence'
            ]
        },
    'AIDA_PHASE3_TASK3_OC_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK3_OC_RESPONSE',
        'year': 2021,
        'task': 'task3',
        'header': ['?root_uid', '?claim_id', '?topic', '?subtopic', '?claim_template', '?description', '?epistemic_status', '?sentiment_status'],
        'columns': [
            'document_id',
            'claim_id',
            'claim_topic',
            'claim_subtopic',
            'claim_template',
            'claim_description',
            'claim_epistemic_status',
            'claim_sentiment_status',
            ]
        },
    'AIDA_PHASE3_TASK3_TM_RESPONSE': {
        'name': 'AIDA_PHASE3_TASK3_TM_RESPONSE',
        'year': 2021,
        'task': 'task3',
        'header': ['?cluster', '?sa_month', '?sa_day', '?sa_year', '?sb_month', '?sb_day', '?sb_year', '?ea_month', '?ea_day', '?ea_year', '?eb_month', '?eb_day', '?eb_year'],
        'columns': [
            'subject_cluster_id',
            'start_after_month',
            'start_after_day',
            'start_after_year',
            'start_before_month',
            'start_before_day',
            'start_before_year',
            'end_after_month',
            'end_after_day',
            'end_after_year',
            'end_before_month',
            'end_before_day',
            'end_before_year'
            ]
        },
    }

def identify_file_schema(fh, task):
    for schema in schemas.values():
        if schema.get('task') != task: continue
        found = 1
        if fh.get('header') is None:
            fh.record_event('EMPTY_FILE_WITHOUT_HEADER', fh.get('filename'), '\t'.join(schema['header']))
        elif len(schema['header']) == len(fh.get('header').get('columns')):
            for i in range(len(schema['header'])):
                if schema['header'][i] != fh.get('header').get('columns')[i]:
                    found = 0
                    break
            if found: return schema
    return None

class ResponseSet(Container):
    """
    Set of responses for AIDA.
    """

    def __init__(self, logger, document_mappings, document_boundaries, path, runid, task='task1', queries=None):
        super().__init__(logger)
        self.claims = Container(logger)
        self.document_mappings = document_mappings
        self.document_boundaries = document_boundaries
        self.validator = Validator(logger)
        self.generator = Generator(logger)
        self.normalizer = Normalizer(logger)
        self.document_clusters = Container(logger)
        self.document_frames = Container(logger)
        self.queries = queries
        self.runid = runid
        self.path = path
        self.task = task
        self.validate_attributes_and_schemas()
        self.load_responses()
        self.validate_responses()

    def load_responses(self):
        method_name = 'load_responses_{task}'.format(task=self.get('task'))
        method = self.get('method', method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name)
        method()

    def load_responses_task1(self):
        def order(filename):
            filename_order_map = {
                'AIDA_P3_TA1_CM_A0001.rq.tsv': 1,
                'AIDA_P3_TA1_AM_A0001.rq.tsv': 2,
                'AIDA_P3_TA1_TM_A0001.rq.tsv': 3
                }
            if filename not in filename_order_map:
                print("Filename: '{}' not found in lookup".format(filename))
                exit()
            return filename_order_map[filename]
        logger = self.get('logger')
        for subdir in tqdm(['{}/{}'.format(self.get('path'), d) for d in os.listdir(self.get('path'))], desc='loading {}'.format(self.get('path'))):
            for filename in sorted(os.listdir(subdir), key=order):
                filename_including_path = '{}/{}'.format(subdir, filename)
                fh = FileHandler(logger, filename_including_path)
                schema = identify_file_schema(fh, self.get('task'))
                if schema is None:
                    logger.record_event('UNKNOWN_RESPONSE_FILE_TYPE', filename_including_path, self.get('code_location'))
                else:
                    self.load_file(fh, schema)

    def load_responses_task2(self):
        logger = self.get('logger')
        path = self.get('path')
        for filename in sorted(os.listdir(path)):
            filename_including_path = '{}/{}'.format(path, filename)
            fh = FileHandler(logger, filename_including_path, encoding='utf-8')
            schema = identify_file_schema(fh, self.get('task'))
            if schema is None:
                logger.record_event('UNKNOWN_RESPONSE_FILE_TYPE', filename_including_path, self.get('code_location'))
            else:
                self.load_file(fh, schema)

    def load_responses_task3(self):
        def get_header(logger, condition, filename):
            if filename.endswith('ranking.tsv'):
                schema_names = {
                    'Condition5': 'AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE',
                    'Condition6': 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE',
                    'Condition7': 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE',
                    }
                header_columns = schemas.get(schema_names.get(condition)).get('header')
                return FileHeader(logger, '\t'.join(header_columns))
        def order(filename):
            filename_order_map = {
                'AIDA_P3_TA3_OC_0001.rq.tsv': 1,
                'AIDA_P3_TA3_CC_0001.rq.tsv': 2,
                'AIDA_P3_TA3_CT_0001.rq.tsv': 3,
                'AIDA_P3_TA3_GR_0001.rq.tsv': 4,
                'AIDA_P3_TA3_TM_0001.rq.tsv': 5,
                'ranking.tsv'               : 6,
                }
            basename = 'ranking.tsv' if filename.endswith('.ranking.tsv') else os.path.basename(filename)
            if basename not in filename_order_map:
                print("Filename: '{}' not found in lookup".format(basename))
                exit()
            return filename_order_map[basename]
        logger = self.get('logger')
        for condition in os.listdir(self.get('path')):
            condition_dir = os.path.join(self.get('path'), condition)
            for query_topic_or_claim_frame_id in os.listdir(condition_dir):
                query_topic_or_claim_frame_dir = os.path.join(condition_dir, query_topic_or_claim_frame_id)
                filenames = set()
                for root, _, files in os.walk(query_topic_or_claim_frame_dir):
                    for filename in sorted([os.path.join(root, file) for file in files], key=order):
                        filenames.add(filename)
                for filename in sorted(filenames, key=order):
                    fh = FileHandler(logger, filename, header=get_header(logger, condition, filename), encoding='utf-8')
                    schema = identify_file_schema(fh, self.get('task'))
                    if schema is None:
                        logger.record_event('UNKNOWN_RESPONSE_FILE_TYPE', filename, self.get('code_location'))
                    else:
                        self.load_file(fh, schema)

    def load_file(self, fh, schema):
        logger = self.get('logger')
        filename = fh.get('filename')
        if not self.exists(filename):
            file_container = Container(logger)
            file_container.set('header', fh.get('header'))
            self.add(key=filename, value=file_container)
        for entry in fh:
            lineno = entry.get('lineno')
            entry.set('runid', self.get('runid'))
            entry.set('schema', schema)
            if self.get('task') == 'task2':
                entry.set('metatype', 'Entity')
            for i in range(len(schema.get('columns'))):
                entry.set(schema.get('columns')[i], entry.get(entry.get('header').get('columns')[i]))
            valid = True
            for attribute_name in attributes:
                attribute = attributes[attribute_name]
                if attribute_name != attribute.get('name'):
                    logger.record_event('DEFAULT_CRITICAL_ERROR',
                                        'Mismatching name of attribute: {}'.format(attribute_name),
                                        self.get_code_location())
                # skip if the attribute is not required for the given schema
                if not self.attribute_required(attribute, schema): continue
                # generate value for the attribute, if needed
                self.generate_value(attribute, entry)
                # normalize value
                normalizer_name = attribute.get('normalize')
                if normalizer_name:
                    self.get('normalizer').normalize(self, normalizer_name, entry, attribute)
                # validate value
                validator_name = attribute.get('validate')
                if validator_name:
                    valid_attribute = self.get('validator').validate(self, validator_name, schema, entry, attribute)
                    if not valid_attribute: valid = False
            entry.set('valid', valid)
            if self.get('task') == 'task3':
                self.get(filename).add(key=str(lineno), value=entry)
            elif entry.get('document_id') in self.get('document_mappings').get('documents') and self.get('document_mappings').get('documents').get(entry.get('document_id')).get('is_core'):
                self.get(filename).add(key=str(lineno), value=entry)

    def attribute_required(self, attribute, schema):
        year = schema.get('year')
        task = schema.get('task')
        if year not in attribute.get('years'): return False
        if task not in attribute.get('tasks'): return False
        if schema.get('name') not in attribute.get('schemas'): return False
        return True

    def generate_value(self, attribute, entry):
        dependencies = attribute.get('dependencies')
        if dependencies:
            for dependency_name in dependencies:
                dependency = attributes[dependency_name]
                self.generate_value(dependency, entry)
        if entry.get(attribute.get('name')):
            return
        generator_name = attribute.get('generate')
        if generator_name:
            self.get('generator').generate(self, generator_name, entry)

    def get_claim(self, claim_uid):
        logger = self.get('logger')
        claims = self.get('claims')
        if claim_uid not in claims:
            claim = Claim(logger, claim_uid)
            claims.add(key=claim_uid, value=claim)
        claim = claims.get(claim_uid)
        return claim

    def get_cluster(self, cluster_id, entry):
        logger = self.get('logger')
        document_id = entry.get('document_id')
        if document_id not in self.get('document_clusters'):
            self.get('document_clusters').add(key=document_id, value=Container(logger))
        document_clusters = self.get('document_clusters').get(document_id)
        if cluster_id not in document_clusters:
            cluster = Cluster(logger, self.get('document_mappings'), self.get('document_boundaries'), cluster_id)
            document_clusters.add(key=cluster_id, value=cluster)
        cluster = document_clusters.get(cluster_id)
        return cluster

    def get_frame(self, frame_id, entry):
        logger = self.get('logger')
        document_id = entry.get('document_id')
        if document_id not in self.get('document_frames'):
            self.get('document_frames').add(key=document_id, value=Container(logger))
        document_frames = self.get('document_frames').get(document_id)
        if frame_id not in document_frames:
            frame = EventOrRelationFrame(logger, frame_id, entry.get('where'))
            document_frames.add(key=frame_id, value=frame)
        frame = document_frames.get(frame_id)
        return frame

    def get_text_boundaries(self):
        return self.get('document_boundaries').get('text')

    def get_image_boundaries(self):
        return self.get('document_boundaries').get('image')

    def get_keyframe_boundaries(self):
        return self.get('document_boundaries').get('keyframe')

    def get_video_boundaries(self):
        return self.get('document_boundaries').get('video')

    def validate_attributes_and_schemas(self):
        for column_name in attributes:
            column_spec = attributes[column_name]
            for schema_name in column_spec.get('schemas'):
                if 'AIDA_PHASE3' in schema_name:
                    if 2021 not in column_spec.get('years'):
                        self.record_event('DEFAULT_CRITICAL_ERROR',
                                            'year \'2021\' should be included in specs for \'{}\''.format(column_name),
                                            self.get_code_location())
        for column_name in attributes:
            column_spec = attributes[column_name]
            for schema_name in column_spec.get('schemas'):
                if schema_name not in schemas:
                    self.record_event('DEFAULT_CRITICAL_ERROR',
                                        'schema not found \'{}\''.format(schema_name),
                                        self.get_code_location())
        for schema in schemas.values():
            for column_name in schema.get('columns'):
                if column_name not in attributes:
                    self.record_event('DEFAULT_CRITICAL_ERROR',
                                        'specs not found for attribute \'{}\''.format(column_name),
                                        self.get_code_location())
                column_spec = attributes[column_name]
                if not self.attribute_required(column_spec, schema):
                    self.record_event('DEFAULT_CRITICAL_ERROR',
                                        'schema \'{}\' does not require attribute \'{}\''.format(schema.get('name'), column_name),
                                        self.get_code_location())

    def validate_responses(self):
        method_name = 'validate_responses_{task}'.format(task=self.get('task'))
        method = self.get('method', method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name)
        method()

    def validate_responses_task1(self):
        # nothing to do here
        return

    def validate_responses_task2(self):
        # nothing to do here
        return

    def validate_responses_task3(self):
        # validate if condition6 and condition7 claims have x-variable
        # validate that rank is unique
        # mark claim as invalid if:
        #   the outer claim is invalid, or
        #   the rank is invalid
        #   xVariable is missing (if required)
        ranks = {}
        for claim in self.get('claims').values():
            claim_uid = claim.get('claim_uid')
            claim_condition = claim.get('claim_condition')
            claim_query_topic_or_claim_frame_id = claim.get('claim_query_topic_or_claim_frame_id')
            if claim.get('outer_claim').get('valid') == False:
                claim.set('valid', False)
            rank_key = '{}:{}'.format(claim_condition, claim_query_topic_or_claim_frame_id)
            claim_rank = claim.get('claim_rank')
            if claim_rank:
                rank = claim_rank.get('rank')
                if rank_key not in ranks:
                    ranks[rank_key] = {}
                if rank in ranks.get(rank_key):
                    claim.set('valid', False)
                    self.record_event('DUPLICATE_VALUE', 'rank: {}'.format(rank), claim.get('claim_rank').get('where'))
                else:
                    ranks.setdefault(rank_key, {})[rank] = claim_uid
            else:
                claim.set('valid', False)
                self.record_event('MISSING_CLAIM_RANK', claim_uid)
            if claim_condition == 'Condition7': continue
            found = False
            for claim_component in claim.get('claim_components'):
                if claim_component.get('claim_component_type') == 'xVariable':
                    found = True
            if not found:
                claim.set('valid', False)
                self.record_event('MISSING_REQUIRED_CLAIM_FIELD', 'xVariable', claim_condition, claim_uid)

    def write_pooled_responses(self, output_dir):
        os.mkdir(output_dir)
        for input_filename in self:
            output_filename = input_filename.replace(self.get('path'), output_dir)
            file_container = self.get(input_filename)
            output_fh = open(output_filename, 'w')
            output_fh.write('{}\n'.format(file_container.get('header').get('line')))
            for linenum in sorted(file_container, key=int):
                entry = self.get(input_filename).get(str(linenum))
                if not entry.get('is_pooled'): continue
                output_fh.write(entry.__str__())
            output_fh.close()

    def write_valid_responses(self, output_dir):
        method_name = 'write_valid_responses_{task}'.format(task=self.get('task'))
        method = self.get('method', method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name)
        method(output_dir)

    def write_valid_responses_task1(self, output_dir):
        os.mkdir(output_dir)
        for input_filename in self:
            output_filename = input_filename.replace(self.get('path'), output_dir)
            dirname = os.path.dirname(output_filename)
            if not os.path.exists(dirname):
                os.mkdir(dirname)
            file_container = self.get(input_filename)
            output_fh = open(output_filename, 'w')
            output_fh.write('{}\n'.format(file_container.get('header').get('line')))
            for linenum in sorted(file_container, key=int):
                entry = self.get(input_filename).get(str(linenum))
                if not entry.get('valid'): continue
                output_fh.write(entry.__str__())
            output_fh.close()

    def write_valid_responses_task2(self, output_dir):
        os.mkdir(output_dir)
        for input_filename in self:
            output_filename = input_filename.replace(self.get('path'), output_dir)
            file_container = self.get(input_filename)
            output_fh = open(output_filename, 'w', encoding='utf-8')
            output_fh.write('{}\n'.format(file_container.get('header').get('line')))
            for linenum in sorted(file_container, key=int):
                entry = self.get(input_filename).get(str(linenum))
                if not entry.get('valid'): continue
                output_fh.write(entry.__str__())
            output_fh.close()

    def write_valid_responses_task3(self, output_dir):
        os.mkdir(output_dir)
        for input_filename in self:
            output_filename = input_filename.replace(self.get('path'), output_dir)
            dirname = os.path.dirname(output_filename)
            if not os.path.exists(dirname):
                os.makedirs(dirname, exist_ok=True)
            file_container = self.get(input_filename)
            output_fh = open(output_filename, 'w', encoding='utf-8')
            if not input_filename.endswith('.ranking.tsv'):
                output_fh.write('{}\n'.format(file_container.get('header').get('line')))
            for linenum in sorted(file_container, key=int):
                entry = self.get(input_filename).get(str(linenum))
                if not entry.get('valid'): continue
                if not entry.get('claim').get('valid'): continue
                output_fh.write(entry.__str__())
            output_fh.close()
