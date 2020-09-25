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
from aida.utility import string_to_span, spanstring_to_object, get_intersection_over_union, augment_mention_object, get_top_level_type

class AnnotatedRegions(Object):
    """
    AIDA annotated regions class.
    """
    def __init__(self, logger, document_mappings, document_boundaries, regions_filename, strictness='strict'):
        super().__init__(logger)
        self.document_mappings = document_mappings
        self.document_boundaries = document_boundaries
        self.filename = regions_filename
        self.regions = Container(logger)
        self.strictness = strictness
        self.load()

    def contains(self, mention, types, metatype):
        method_name = 'contains_{}'.format(self.get('strictness'))
        method = self.get_method(method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name)
        return method(mention, types, metatype)

    def contains_relaxed(self, mention, types, metatype):
        document_id = mention.get('document_id')
        document_element_id = mention.get('document_element_id')
        keyframe_id = mention.get('keyframe_id')
        doce_or_kf_id = keyframe_id if keyframe_id else document_element_id
        for cluster_type in types:
            top_level_type = get_top_level_type(cluster_type, metatype)
            for key in self.get('regions'):
                document_id_, doce_or_kf_id_, cluster_type_ = key.split(':')
                top_level_type_ = get_top_level_type(cluster_type_, metatype)
                if document_id != document_id_: continue
                if doce_or_kf_id != doce_or_kf_id_: continue
                if top_level_type != top_level_type_: continue
                for region_string in [s.__str__() for s in self.get('regions').get(key)]:
                    fq_region_string = '{docid}:{doce_or_kf_id}:{span_string}'.format(docid=document_id_,
                                                           doce_or_kf_id=doce_or_kf_id_,
                                                           region_string=region_string)
                    region = augment_mention_object(spanstring_to_object(self.logger, fq_region_string), self.get('document_mappings'), self.get('document_boundaries'))
                    if get_intersection_over_union(mention, region) > 0:
                        return True
        return False

    def contains_strict(self, mention, types, metatype):
        document_element_id = mention.get('document_element_id')
        keyframe_id = mention.get('keyframe_id')
        for cluster_type in types:
            key = '{docid}:{doce_or_kf_id}:{cluster_type}'.format(docid=mention.get('document_id'),
                                                           doce_or_kf_id=keyframe_id if keyframe_id else document_element_id,
                                                           cluster_type=cluster_type)
            if key not in self.get('regions'): continue
            for span_string in self.get('regions').get(key):
                fq_span_string = '{docid}:{doce_or_kf_id}:{span_string}'.format(docid=mention.get('document_id'),
                                                           doce_or_kf_id=keyframe_id if keyframe_id else document_element_id,
                                                           span_string=span_string)
                region = augment_mention_object(spanstring_to_object(self.logger, fq_span_string), self.get('document_mappings'), self.get('document_boundaries'))
                if get_intersection_over_union(mention, region) > 0:
                    return True
        return False

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