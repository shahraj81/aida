"""
Generator for generated-values in AIDA response.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "24 January 2020"

from aida.container import Container
from aida.object import Object
from aida.utility import get_kb_document_id_from_filename, spanstring_to_object, trim

class Generator(Object):
    """
    Generator for generated-values in AIDA response.
    """

    def __init__(self, logger):
        super().__init__(logger)

    def generate(self, responses, method_name, entry):
        method = self.get_method(method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name)
        method(responses, entry)

    def generate_cluster(self, responses, entry):
        cluster_id = entry.get('cluster_id')
        cluster = responses.get('cluster', cluster_id, entry)
        if entry.get('schema').get('name') in ['AIDA_PHASE2_TASK1_CM_RESPONSE']:
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

    def generate_document_id(self, responses, entry):
        document_id = None
        if entry.get('kb_document_id'):
            document_id = entry.get('kb_document_id')
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
        date_fields = ['month', 'day', 'year']
        date_field_values = {key: trim(entry.get(field_name))
                                for key, field_name in {key:'{}_{}'.format(date_name, key) for key in date_fields}.items()}
        date_object = Object(entry.get('logger'))
        present = False
        for date_field in date_fields:
            date_object.set(date_field, None if date_field_values[date_field]=='' else int(date_field_values[date_field]))
            if date_object.get(date_field): present = True
        # consider all date fields to be missing if year was missing even if day and month were provided
        if present and not date_object.get('year'): present = False
        if present and date_object.get('day') and not date_object.get('month'):
            date_object.set('day', None)
        return date_object if present else None

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

    def generate_kb_document_id(self, responses, entry):
        kb_document_id = get_kb_document_id_from_filename(entry.get('filename'))
        entry.set('kb_document_id', kb_document_id)

    def generate_object_cluster(self, responses, entry):
        cluster_id = entry.get('object_cluster_id')
        cluster = responses.get('cluster', cluster_id, entry)
        entry.set('object_cluster', cluster)

    def generate_start(self, responses, entry):
        entry.set('start', self.get('date_range', responses, entry, 'start'))

    def generate_start_after(self, responses, entry):
        entry.set('start_after', self.get('date', responses, entry, 'start_after'))

    def generate_start_before(self, responses, entry):
        entry.set('start_before', self.get('date', responses, entry, 'start_before'))

    def generate_subject_cluster(self, responses, entry):
        cluster_id = entry.get('subject_cluster_id')
        cluster = responses.get('cluster', cluster_id, entry)
        if not cluster.get('frame'):
            frame = responses.get('frame', cluster_id, entry)
            cluster.set('frame', frame)
        frame = cluster.get('frame')
        frame.update(entry)
        entry.set('subject_cluster', cluster)