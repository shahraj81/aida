"""
Validator for values in AIDA response.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 January 2022"

from aida.object import Object
from aida.span import Span
from aida.utility import types_are_compatible, is_number, trim_cv

import datetime
import os
import re

class Validator(Object):
    """
    Validator for values in AIDA response.
    """

    def __init__(self, logger):
        super().__init__(logger)

    def parse_provenance(self, provenance):
        pattern = re.compile('^(\w+?):(\w+?):\((\S+),(\S+)\)-\((\S+),(\S+)\)$')
        match = pattern.match(provenance)
        if not match: return
        document_id = match.group(1)
        document_element_id = match.group(2)
        start_x, start_y, end_x, end_y = map(lambda ID: match.group(ID), [3, 4, 5, 6])

        # if provided, obtain keyframe_id and update document_element_id
        pattern = re.compile('^(\w*?)_(\d+)$')
        match = pattern.match(document_element_id)
        keyframe_num = match.group(2) if match else None
        document_element_id = match.group(1) if match else document_element_id

        return document_id, document_element_id, keyframe_num, start_x, start_y, end_x, end_y

    def validate(self, responses, method_name, schema, entry, attribute):
        method = self.get_method(method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name)
        return method(responses, schema, entry, attribute)

    def validate_claim_id(self, responses, schema, entry, attribute):
        claim_id = entry.get(attribute.get('name'))
        kb_claim_id = entry.get('kb_claim_id')
        if claim_id != kb_claim_id:
            self.record_event('UNEXPECTED_CLAIM_ID', kb_claim_id, claim_id, entry.get('where'))
        if claim_id not in responses.get('claims'):
            self.record_event('UNKNOWN_CLAIM_ID', claim_id, entry.get('where'))

    def validate_claim_component_type(self, responses, schema, entry, attribute):
        allowed_values = ['claimMedium', 'claimer', 'claimerAffiliation', 'claimLocation', 'xVariable']
        return self.get('validate_set_membership', 'component_type', allowed_values, entry.get(attribute.get('name')), entry.get('where'))

    def validate_claim_epistemic_status(self, responses, schema, entry, attribute):
        allowed_values = ['EpistemicTrueCertain', 'EpistemicTrueUncertain', 'EpistemicFalseCertain', 'EpistemicFalseUncertain', 'EpistemicUnknown']
        return self.get('validate_set_membership', 'epistemic_status', allowed_values, entry.get(attribute.get('name')), entry.get('where'))

    def validate_claim_sentiment_status(self, responses, schema, entry, attribute):
        allowed_values = ['SentimentPositive', 'SentimentNegative', 'SentimentMixed', 'SentimentNeutralUnknown']
        return self.get('validate_set_membership', 'sentiment_status', allowed_values, entry.get(attribute.get('name')), entry.get('where'))

    def validate_cluster_type(self, responses, schema, entry, attribute):
        logger = self.get('logger')
        cluster_type = entry.get(attribute.get('name'))
        if not responses.get('ontology_type_mappings').has(entry.get('metatype'), cluster_type):
            logger.record_event('UNKNOWN_TYPE', cluster_type, entry.get('where'))
            return False
        return True

    def validate_coordinates(self, provenance, start_x, start_y, end_x, end_y, where):
        for coordinate in [start_x, start_y, end_x, end_y]:
            if not is_number(coordinate):
                self.record_event('NOT_A_NUMBER', coordinate, where)
                return False
            if float(coordinate) < 0:
                self.record_event('NEGATIVE_NUMBER', coordinate, where)
                return False
        for start, end in [(start_x, end_x), (start_y, end_y)]:
            if float(start) > float(end):
                self.record_event('START_BIGGER_THAN_END', start, end, provenance, where)
                return False
        return True

    def validate_document_id(self, responses, schema, entry, attribute):
        logger = self.get('logger')
        document_id = entry.get('document_id')
        if document_id is None:
            logger.record_event('MISSING_ITEM', 'document_id', entry.get('where'))
            return False
        if entry.get('object_informative_justification') and document_id != entry.get('object_informative_justification').get('document_id'):
            logger.record_event('MULTIPLE_ITEMS', 'document_ids', document_id, entry.get('object_informative_justification'), entry.get('where'))
            return False
        if entry.get('predicate_justification') and document_id != entry.get('predicate_justification').get('document_id'):
            logger.record_event('MULTIPLE_ITEMS', 'document_ids', document_id, entry.get('predicate_justification'), entry.get('where'))
            return False
        if not responses.get('document_mappings').get('documents').exists(document_id):
            self.record_event('UNKNOWN_ITEM', 'document', document_id, entry.get('where'))
            return False
        if schema.get('task') == 'task1':
            kb_document_id = entry.get('kb_document_id')
            if document_id != kb_document_id:
                self.record_event('UNEXPECTED_DOCUMENT', kb_document_id, document_id, entry.get('where'))
                return False
        return True

    def validate_kb_claim_id(self, responses, schema, entry, attribute):
        return self.validate_claim_id(responses, schema, entry, attribute)

    def validate_kb_document_id(self, responses, schema, entry, attribute):
        return self.validate_document_id(responses, schema, entry, attribute)

    def validate_entity_type_in_response(self, responses, schema, entry, attribute):
        entity_type_in_query = entry.get('query').get('entity_type')
        entity_type_in_response = entry.get('entity_type_in_response')
        expected_entity_type = '{0} or {0}.*'.format(entity_type_in_query)
        if not types_are_compatible(entity_type_in_query, entity_type_in_response):
            self.record_event('UNEXPECTED_ENTITY_TYPE', expected_entity_type, entity_type_in_response, entry.get('where'))
        return True

    def validate_entity_type_in_query(self, responses, schema, entry, attribute):
        entity_type_in_query = entry.get('query').get('entity_type')
        query_entity_type_in_response = entry.get('entity_type_in_query')
        if entity_type_in_query != query_entity_type_in_response:
            self.record_event('UNEXPECTED_ENTITY_TYPE', entity_type_in_query, query_entity_type_in_response, entry.get('where'))
        return True

    def validate_importance_value(self, responses, schema, entry, attribute):
        importance_value = entry.get(attribute.get('name'))
        try:
            value = trim_cv(importance_value)
        except ValueError:
            self.record_event('INVALID_IMPORTANCE_VALUE', importance_value, entry.get('where'))
            return False
        return True

    def validate_metatype(self, responses, schema, entry, attribute):
        allowed_metatypes = ['Entity', 'Relation', 'Event']
        metatype = entry.get(attribute.get('name'))
        if metatype not in allowed_metatypes:
            self.record_event('INVALID_METATYPE', metatype, ','.join(allowed_metatypes), entry.get('where'))
            return False
        if attribute.get('name') == 'subject_cluster_member_metatype' and metatype == 'Entity':
            self.record_event('UNEXPECTED_VALUE', 'metatype', metatype, entry.get('where'))
            return False
        cluster = entry.get('cluster')
        if cluster and cluster.get('metatype') != metatype:
            return False
        if entry.get('schema').get('name') == 'AIDA_PHASE2_TASK1_AM_RESPONSE' and metatype == 'Entity':
            self.record_event('UNEXPECTED_VALUE', 'metatype', metatype, entry.get('where'))
            return False
        return True

    def validate_negation_status(self, responses, schema, entry, attribute):
        allowed_values = ['Negated', 'NotNegated']
        return self.get('validate_set_membership', 'negation_status', allowed_values, entry.get(attribute.get('name')), entry.get('where'))

    def validate_object_type(self, responses, schema, entry, attribute):
        # Do not validate object type in Phase 3
        return True

    def validate_predicate(self, responses, schema, entry, attribute):
        logger = self.get('logger')
        predicate = entry.get(attribute.get('name'))
        if not responses.get('slot_mappings').get('type_to_codes', predicate):
            self.record_event('UNKNOWN_PREDICATE', predicate, entry.get('where'))
            return False
        if len(predicate.split('_')) != 2:
            self.record_event('INVALID_PREDICATE_NO_UNDERSCORE', predicate, entry.get('where'))
            return False
        subject_type, rolename = predicate.split('_')
        valid_subject_type = False
        if schema.get('task') == 'task3':
            for metatype in ['Event', 'Relation']:
                if responses.get('ontology_type_mappings').has(metatype, subject_type):
                    valid_subject_type = True
        elif responses.get('ontology_type_mappings').has(entry.get('metatype'), subject_type):
            valid_subject_type = True
        if not valid_subject_type:
            logger.record_event('UNKNOWN_TYPE', subject_type, entry.get('where'))
            return False
        if schema.get('task')!= 'task3' and subject_type not in entry.get('subject_cluster').get('types'):
            logger.record_event('UNEXPECTED_SUBJECT_TYPE', subject_type, entry.get('subject_cluster').get('ID'), entry.get('where'))
            return False
        if entry.get('metatype') == 'Relation'and entry.get('subject_cluster').get('frame').get('number_of_fillers') > 2:
                self.record_event('IMPROPER_RELATION', entry.get('subject_cluster').get('ID'), entry.get('where'))
        return True

    def validate_provenance_format(self, provenance, where):
        if len(provenance.split(':')) != 3:
            self.record_event('INVALID_PROVENANCE_FORMAT', provenance, where)
            return False
        pattern = re.compile('^(\w+?):(\w+?):\((\S+),(\S+)\)-\((\S+),(\S+)\)$')
        match = pattern.match(provenance)
        if not match:
            self.record_event('INVALID_PROVENANCE_FORMAT', provenance, where)
            return False
        return True

    def validate_set_membership(self, name, allowed_values, value, where):
        if value not in allowed_values:
            self.record_event('UNKNOWN_VALUE', name, value, ','.join(sorted(allowed_values)), where)
            return False
        return True

    def validate_subject_type(self, responses, schema, entry, attribute):
        # Do not validate subject type in Phase 3
        return True

    def validate_entries_in_cluster(self, responses, schema, entry, attribute):
        cluster = entry.get(attribute.get('name'))
        valid = False
        for entry in cluster.get('entries').values():
            if entry.get('valid'):
                valid = True
        return valid

    def validate_before_and_after_dates(self, responses, schema, entry, attribute, start_or_end_before, before, start_or_end_after, after):
        valid = True
        problem_field = None
        if before.get('year') < after.get('year'):
            problem_field = 'year'
            valid = False
        elif before.get('year') == after.get('year'):
            if before.get('month') and after.get('month'):
                if before.get('month') < after.get('month'):
                    problem_field = 'month'
                    valid = False
                elif before.get('month') == after.get('month'):
                    if before.get('day') and after.get('day') and before.get('day') < after.get('day'):
                        problem_field = 'day'
                        valid = False
        if not valid:
            self.record_event('INVALID_DATE_RANGE', entry.get('subject_cluster_id'), start_or_end_after, start_or_end_before, entry.get('where'))
        return valid

    def validate_date_start_and_end(self, responses, schema, entry, attribute):
        valid = True
        if entry.get('date'):
            start = entry.get('date').get('start')
            end = entry.get('date').get('end')
            if start and end:
                start_after = start.get('after')
                end_before = end.get('before')
                if start_after and end_before:
                    valid = self.validate_before_and_after_dates(responses, schema, entry, attribute, 'end_before', end_before, 'start_after', start_after)
        return valid

    def validate_date(self, responses, schema, entry, attribute):
        valid = True
        date_object = entry.get(attribute.get('name'))
        if date_object:
            year = date_object.get('year')
            month = date_object.get('month')
            day = date_object.get('day')
            if year and month and day:
                try:
                    datetime.date(int(year), int(month), int(day))
                except:
                    self.record_event('INVALID_DATE', entry.get('cluster_id'), attribute.get('name'), 'date', entry.get('where'))
                    return False
            elif year < 0:
                self.record_event('INVALID_DATE', entry.get('cluster_id'), attribute.get('name'), 'date', entry.get('where'))
                valid = False
            elif month and not 1 <= month <= 12:
                self.record_event('INVALID_DATE', entry.get('cluster_id'), attribute.get('name'), 'date', entry.get('where'))
                valid = False
        return valid

    def validate_date_range(self, responses, schema, entry, attribute):
        after = entry.get('{}_after'.format(attribute.get('name')))
        before = entry.get('{}_before'.format(attribute.get('name')))
        valid = True
        if after and before:
            valid = self.validate_before_and_after_dates(responses, schema, entry, attribute, '{}_before'.format(attribute.get('name')), before, '{}_after'.format(attribute.get('name')), after)
        return valid

    def validate_value_provenance_triple(self, responses, schema, entry, attribute):
        return self.validate_provenance(responses,
                                         schema,
                                         entry,
                                         attribute.get('name'),
                                         entry.get(attribute.get('name')),
                                         apply_correction=True)

    def validate_value_provenance_triples(self, responses, schema, entry, attribute):
        provenances = entry.get(attribute.get('name')).split(';')
        apply_correction = True if len(provenances) == 1 else False
        if len(provenances) > 2:
            self.record_event('IMPROPER_COMPOUND_JUSTIFICATION', entry.get(attribute.get('name')), entry.get('where'))
            return False
        for provenance in provenances:
            if not self.validate_provenance(responses,
                                            schema,
                                            entry,
                                            attribute.get('name'),
                                            provenance,
                                            apply_correction=apply_correction):
                return False
        return True

    def validate_provenance(self, responses, schema, entry, attribute_name, provenance, apply_correction):
        where = entry.get('where')

        if schema.get('task') == 'task3' and attribute_name == 'subject_informative_justification_span_text' and provenance == 'NULL':
            return True

        if schema.get('task') == 'task3' and attribute_name == 'predicate_justification_spans_text' and provenance == 'NULL':
            return True

        if not self.validate_provenance_format(provenance, where):
            return False

        document_id, document_element_id, keyframe_num, start_x, start_y, end_x, end_y = self.parse_provenance(provenance)

        # check if the document element has file extension appended to it
        # if so, report warning, and apply correction
        extensions = tuple(['.' + extension for extension in responses.get('document_mappings').get('encodings')])
        if document_element_id.endswith(extensions):
            if apply_correction:
                self.record_event('ID_WITH_EXTENSION', 'document element id', document_element_id, where)
                document_element_id = os.path.splitext(document_element_id)[0]
                provenance = '{}:{}:({},{})-({},{})'.format(document_id, document_element_id, start_x, start_y, end_x, end_y)
                entry.set(attribute_name, provenance)
            else:
                self.record_event('ID_WITH_EXTENSION_ERROR', 'document element id', document_element_id, where)
                return False

        if document_id != entry.get('document_id'):
            self.record_event('MULTIPLE_DOCUMENTS', document_id, entry.get('document_id'), where)
            return False

        documents = responses.get('document_mappings').get('documents')
        document_elements = responses.get('document_mappings').get('document_elements')

        if document_id not in documents:
            self.record_event('UNKNOWN_ITEM', 'document', document_id, where)
            return False
        document = documents.get(document_id)

        if document_element_id not in document_elements:
            self.record_event('UNKNOWN_ITEM', 'document element', document_element_id, where)
            return False
        document_element = document_elements.get(document_element_id)

        modality = document_element.get('modality')
        if modality is None:
            self.record_event('UNKNOWN_MODALITY', document_element_id, where)
            return False

        keyframe_id = None
        if modality == 'video':
            if keyframe_num:
                keyframe_id = '{}_{}'.format(document_element_id, keyframe_num)
                if keyframe_id not in responses.get('keyframe_boundaries'):
                    self.record_event('MISSING_ITEM_WITH_KEY', 'KeyFrameID', keyframe_id, where)
                    return False

        if not document.get('document_elements').exists(document_element_id):
            self.record_event('PARENT_CHILD_RELATION_FAILURE', document_element_id, document_id, where)
            return False

        if not self.validate_coordinates(provenance, start_x, start_y, end_x, end_y, where):
            return False

        # An entry in the coreference metric output file is invalid if:
        #  (a) a video mention of an entity was asserted using VideoJustification, or
        #  (b) a video mention of an relation/event was asserted using KeyFrameVideoJustification
        if entry.get('schema').get('name') in ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE2_TASK2_ZH_RESPONSE'] and modality == 'video':
            if keyframe_id and entry.get('metatype') != 'Entity':
                self.record_event('UNEXPECTED_JUSTIFICATION', provenance, entry.get('metatype'), entry.get('cluster_id'), 'KeyFrameVideoJustification', entry.get('where'))
                return False
            elif not keyframe_id and entry.get('metatype') not in ['Relation', 'Event']:
                self.record_event('UNEXPECTED_JUSTIFICATION', provenance, entry.get('metatype'), entry.get('cluster_id'), 'VideoJustification', entry.get('where'))
                return False

        document_element_boundary = responses.get('{}_boundaries'.format('keyframe' if modality=='video' and keyframe_id else modality)).get(keyframe_id if modality == 'video' and keyframe_id else document_element_id)
        span = Span(self.logger, start_x, start_y, end_x, end_y)
        if not document_element_boundary.validate(span):
            corrected_span = document_element_boundary.get('corrected_span', span)
            if corrected_span is None or not apply_correction:
                self.record_event('SPAN_OFF_BOUNDARY_ERROR', span, document_element_boundary, document_element_id, where)
                return False
            corrected_provenance = '{}:{}:{}'.format(document_id, keyframe_id if keyframe_id else document_element_id, corrected_span.__str__())
            entry.set(attribute_name, corrected_provenance)
            self.record_event('SPAN_OFF_BOUNDARY_CORRECTED', span, corrected_span, document_element_boundary, document_element_id, where)
        return True
    
    def validate_confidence(self, responses, schema, entry, attribute):
        confidence_value = entry.get(attribute.get('name'))
        if schema.get('task') == 'task3' and schema.get('name') == 'AIDA_PHASE2_TASK3_GR_RESPONSE' and attribute.get('name') == 'predicate_justification_confidence' and confidence_value == 'NULL':
            return True
        try:
            value = trim_cv(confidence_value)
        except ValueError:
            self.record_event('INVALID_CONFIDENCE', entry.get(attribute.get('name')), entry.get('where'))
            value = 1.0
            entry.set(attribute.get('name'), '"{value}"'.format(value=value))
        if not 0 < value <= 1:
            self.record_event('INVALID_CONFIDENCE', value, entry.get('where'))
            value = 1.0
            entry.set(attribute.get('name'), '"{value}"'.format(value=value))
        return True