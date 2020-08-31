"""
AIDA annotated regions class.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "20 July 2020"

from aida.object import Object
from aida.container import Container
from aida.file_handler import FileHandler
from aida.utility import string_to_span, spanstring_to_object, get_intersection_over_union, augment_mention_object

class AnnotatedRegions(Object):
    """
    AIDA annotated regions class.
    """
    def __init__(self, logger, document_mappings, document_boundaries, regions_filename):
        super().__init__(logger)
        self.document_mappings = document_mappings
        self.document_boundaries = document_boundaries
        self.filename = regions_filename
        self.regions = Container(logger)
        self.load()

    def contains(self, mention, types):
        contains = False
        for cluster_type in types:
            document_element_id = mention.get('document_element_id')
            keyframe_id = mention.get('keyframe_id')
            key = '{docid}:{doce_or_kf_id}:{cluster_type}'.format(docid=mention.get('document_id'),
                                                           doce_or_kf_id=keyframe_id if keyframe_id else document_element_id,
                                                           cluster_type=cluster_type)
            if key not in self.get('regions'): continue
            for span_string in self.get('regions').get(key):
                span_string = '{docid}:{doce_or_kf_id}:{span_string}'.format(docid=mention.get('document_id'),
                                                           doce_or_kf_id=keyframe_id if keyframe_id else document_element_id,
                                                           span_string=span_string)
                region = augment_mention_object(spanstring_to_object(self.logger, span_string), self.get('document_mappings'), self.get('document_boundaries'))
                if get_intersection_over_union(mention, region) > 0:
                    contains = True
        return contains

    def get_entry_to_key(self, entry):
        return ':'.join([entry.get('document_id'), entry.get('document_element_or_keyframe_id'), entry.get('type')])

    def get_entry_to_spans(self, entry):
        logger = self.get('logger')
        spans = Container(logger)
        for span_string in entry.get('region').split(';'):
            span = string_to_span(logger, span_string, entry.get('where'))
            span.set('modality', self.get(''))
            spans.add(key=span, value=span)
        return spans

    def get_types_annotated_for_document(self, document_id):
        types = {}
        for key in self.get('regions'):
            elements = key.split(':')
            if elements[0] == document_id:
                types[elements[2]] = 1
        return set(list(types.keys()))

    def load(self):
        logger = self.get('logger')
        for entry in FileHandler(logger, self.get('filename')):
            key = self.get('entry_to_key', entry)
            if key not in self.get('regions'):
                self.get('regions').add(key=key, value=Container(logger))
            regions_by_key = self.get('regions').get(key)
            for span in self.get('entry_to_spans', entry):
                regions_by_key.add(key=span, value=span)