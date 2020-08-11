"""
Generator for generated-values in AIDA response.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "24 January 2020"

from aida.container import Container
from aida.object import Object
from aida.utility import get_kb_document_id_from_filename, spanstring_to_object

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

    def generate_kb_document_id(self, responses, entry):
        kb_document_id = get_kb_document_id_from_filename(entry.get('filename'))
        entry.set('kb_document_id', kb_document_id)

    def generate_object_cluster(self, responses, entry):
        cluster_id = entry.get('object_cluster_id')
        cluster = responses.get('cluster', cluster_id, entry)
        entry.set('object_cluster', cluster)

    def generate_subject_cluster(self, responses, entry):
        cluster_id = entry.get('subject_cluster_id')
        cluster = responses.get('cluster', cluster_id, entry)
        if not cluster.get('frame'):
            frame = responses.get('frame', cluster_id, entry)
            cluster.set('frame', frame)
        frame = cluster.get('frame')
        frame.update(entry)
        entry.set('subject_cluster', cluster)