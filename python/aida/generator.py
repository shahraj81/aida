"""
Generator for generated-values in AIDA response.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 January 2022"

from aida.container import Container
from aida.ldc_time import LDCTime
from aida.object import Object
from aida.utility import get_kb_claim_id_from_filename, get_kb_document_id_from_filename, spanstring_to_object, trim

import os

class Generator(Object):
    """
    Generator for generated-values in AIDA response.
    """

    def __init__(self, logger):
        super().__init__(logger)

    def generate(self, responses, method_name, entry):
        method = self.get('method', method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name)
        method(responses, entry)

    def generate_claim_component_key(self, responses, entry):
        claim_id = entry.get('claim_id')
        claim_component_type = entry.get('claim_component_type')
        claim_component_name = entry.get('claim_component_name')
        claim_component_qnode_id = entry.get('claim_component_qnode_id')
        entry.set('claim_component_key', ':'.join([claim_id, claim_component_type, claim_component_name, claim_component_qnode_id]))

    def generate_claim_component_qnode_types(self, responses, entry):
        claim = entry.get('claim')
        if claim.get('claim_component_qnode_types') is None:
            claim.set('claim_component_qnode_types', {})
        claim_component_qnode_types = claim.get('claim_component_qnode_types')
        claim_component_key = entry.get('claim_component_key')
        if claim_component_key not in claim_component_qnode_types:
            claim_component_qnode_types[claim_component_key] = set()
        claim_component_qnode_types[claim_component_key].add(entry.get('claim_component_qnode_type'))
        entry.set('claim_component_qnode_types', claim_component_qnode_types[claim_component_key])

    def generate_cluster(self, responses, entry):
        cluster_id = entry.get('cluster_id')
        cluster = responses.get('cluster', cluster_id, entry)
        if entry.get('schema').get('name') in ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_CM_RESPONSE']:
            cluster.add(entry)
        entry.set('cluster', cluster)

    def generate_date_start_and_end(self, response, entry):
        date_object = Object(entry.get('logger'))
        present = False
        for field_name in ['start', 'end']:
            if entry.get(field_name):
                present = True
                date_object.set(field_name, entry.get(field_name))
        entry.set('date', date_object if present else None)
        if entry.get('schema').get('name') in ['AIDA_PHASE2_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE']:
            entry.get('subject_cluster').get('dates').add(entry.get('date'))

    def generate_claim(self, responses, entry):
        claim_uid = entry.get('claim_uid')
        claim = None
        if not (entry.get('schema').get('name') in ['AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE'] and claim_uid not in responses.get('claims')):
            claim = responses.get('claim', claim_uid)
            claim.update(entry)
        entry.set('claim', claim)

    def generate_claim_id(self, responses, entry):
        claim_id = None
        if claim_id is None:
            claim_id = entry.get('kb_claim_id')
        entry.set('claim_id', claim_id)

    def generate_claim_uid(self, responses, entry):
        entry.set('claim_uid', self.get_claim_uid(entry))

    def generate_claim_condition(self, responses, entry):
        filename = entry.get('filename')
        claim_condition = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(filename))))
        if entry.get('schema').get('name') in ['AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE']:
            claim_condition = os.path.basename(os.path.dirname(os.path.dirname(filename)))
        entry.set('claim_condition', claim_condition)

    def generate_claim_query_topic_or_claim_frame_id(self, responses, entry):
        filename = entry.get('filename')
        claim_query_topic_or_claim_frame_id = os.path.basename(os.path.dirname(os.path.dirname(filename)))
        if entry.get('schema').get('name') in ['AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE']:
            claim_query_topic_or_claim_frame_id = os.path.basename(os.path.dirname(filename))
        entry.set('claim_query_topic_or_claim_frame_id', claim_query_topic_or_claim_frame_id)

    def generate_document_id(self, responses, entry):
        document_id = None
        if entry.get('kb_document_id'):
            document_id = entry.get('kb_document_id')
        elif entry.get('claim_uid'):
            claim = responses.get('claims').get(entry.get('claim_uid'))
            document_id = claim.get('outer_claim').get('document_id')
        elif entry.get('object_informative_justification_span_text'):
            span_object = spanstring_to_object(entry.get('logger'), entry.get('object_informative_justification_span_text'))
            document_id = span_object.get('document_id')
        elif entry.get('predicate_justification_span_text'):
            span_object = spanstring_to_object(entry.get('logger'), entry.get('predicate_justification_span_text'))
            document_id = span_object.get('document_id')
        elif entry.get('mention_span_text'):
            span_object = spanstring_to_object(entry.get('logger'), entry.get('mention_span_text'))
            document_id = span_object.get('document_id')
        entry.set('document_id', document_id)

    def generate_end(self, responses, entry):
        entry.set('end', self.get('date_range', responses, entry, 'end'))

    def get_date(self, responses, entry, date_name):
        date_fields = {'month': 'xx', 'day':'xx', 'year':'xxxx'}
        date_field_values = {key: trim(entry.get(field_name))
                                for key, field_name in {key:'{}_{}'.format(date_name, key) for key in date_fields}.items()}
        field_names_missing = []
        date_object = Object(entry.get('logger'))
        for date_field in date_fields:
            date_object.set(date_field, None if date_field_values[date_field]=='' else int(date_field_values[date_field]))
            if date_field_values[date_field]=='':
                field_names_missing.append(date_field)
                date_field_values[date_field] = date_fields[date_field]

        if len(field_names_missing) > 0:
            unspecified_date = '{year}-{month}-{day}'.format(day=date_field_values['day'],
                                                             month=date_field_values['month'],
                                                             year=date_field_values['year'])
            start_or_end, before_or_after = date_name.split('_')
            corrected_date = LDCTime(self.get('logger'), unspecified_date, start_or_end, before_or_after, entry.get('where'))
            # update date_object
            if 'year' in field_names_missing:
                date_object = None
            else:
                missing_fields = ','.join(field_names_missing)
                self.record_event('MISSING_DATE_FIELD', date_name, missing_fields, corrected_date.__str__(), date_name, entry.get('where'))
                for date_field in date_fields:
                    date_object.set(date_field, int(corrected_date.get(date_field).__str__()))
                    entry.set('{}_{}'.format(date_name, date_field), '"{}"'.format(corrected_date.get(date_field).__str__()))
        return date_object

    def get_date_range(self, responses, entry, date_name):
        date_range = Object(entry.get('logger'))
        present = False
        for range_field in ['before', 'after']:
            date_range.set(range_field, entry.get('{}_{}'.format(date_name, range_field)))
            if date_range.get(range_field): present = True
        return date_range if present else None

    def generate_end_after(self, responses, entry):
        entry.set('end_after', self.get('date', responses, entry, 'end_after'))

    def generate_end_before(self, responses, entry):
        entry.set('end_before', self.get('date', responses, entry, 'end_before'))

    def generate_kb_claim_id(self, responses, entry):
        if entry.get('schema').get('name') in ['AIDA_PHASE3_TASK3_CONDITION5_RANKING_RESPONSE', 'AIDA_PHASE3_TASK3_CONDITION67_RANKING_RESPONSE']:
            return
        kb_claim_id = get_kb_claim_id_from_filename(entry.get('filename'))
        entry.set('kb_claim_id', kb_claim_id)

    def generate_kb_document_id(self, responses, entry):
        if entry.get('schema').get('name') in ['AIDA_PHASE2_TASK3_GR_RESPONSE',
                                               'AIDA_PHASE3_TASK3_TM_RESPONSE']:
            return
        if entry.get('schema').get('name') == 'AIDA_PHASE2_TASK2_ZH_RESPONSE':
            return
        kb_document_id = get_kb_document_id_from_filename(entry.get('filename'))
        entry.set('kb_document_id', kb_document_id)

    def generate_object_cluster(self, responses, entry):
        cluster_id = entry.get('object_cluster_id')
        cluster = responses.get('cluster', cluster_id, entry)
        entry.set('object_cluster', cluster)

    def generate_query_claim_uid(self, responses, entry):
        entry.set('query_claim_uid', self.get_claim_uid(entry))

    def generate_start(self, responses, entry):
        entry.set('start', self.get('date_range', responses, entry, 'start'))

    def generate_start_after(self, responses, entry):
        entry.set('start_after', self.get('date', responses, entry, 'start_after'))

    def generate_start_before(self, responses, entry):
        entry.set('start_before', self.get('date', responses, entry, 'start_before'))

    def generate_subject_cluster(self, responses, entry):
        if entry.get('schema').get('name') not in ['AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_TM_RESPONSE', 'AIDA_PHASE3_TASK3_TM_RESPONSE', 'AIDA_PHASE2_TASK1_TM_RESPONSE']:
            return
        cluster_id = entry.get('subject_cluster_id')
        cluster = responses.get('cluster', cluster_id, entry)
        if not cluster.get('frame'):
            frame = responses.get('frame', cluster_id, entry)
            cluster.set('frame', frame)
        frame = cluster.get('frame')
        if entry.get('schema').get('name') in ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE']:
            frame.update(entry)
        entry.set('subject_cluster', cluster)

    def get_claim_uid(self, entry):
        fields = ['claim_condition', 'claim_query_topic_or_claim_frame_id', 'claim_id']
        return ':'.join([entry.get(f) for f in fields])