"""
AIDA mention class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "2 January 2020"

from aida.object import Object
from aida.document_span import DocumentSpan
from aida.utility import is_number
from aida.ere_spec import unspecified
import re

class Mention(Object):
    """
    AIDA mention class.
    """

    def __init__(self, logger, document_mappings, text_boundaries, image_boundaries, video_boundaries, keyframe_boundaries, type_mappings, load_video_time_offsets_flag, entry):
        super().__init__(logger)
        self.logger = logger
        # roll up relevant information from entry into mention
        self.header = entry.get('header')
        self.entry = entry
        self.where = entry.get('where')
        self.document_mappings = document_mappings
        self.text_boundaries = text_boundaries
        self.image_boundaries = image_boundaries
        self.video_boundaries = video_boundaries
        self.keyframe_boundaries = keyframe_boundaries
        self.type_mappings = type_mappings
        self.load_video_time_offsets_flag = load_video_time_offsets_flag
        # the set of nodes that are referred to by this mention
        self.nodes = {}
        # the document spans included in this mention
        self.document_spans = {}
        # set the span of text, or image bounding box of the 
        # mention
        self.load_document_spans()
        # set the 'node_metatype' (i.e. ENTITY, RELATION, or 
        # ENTITY) of the nodes referred to by this mention
        self.load_node_metatype()

    def get_cleaned_full_type(self):
        cleaned_full_type = self.type_mappings.get(self.get('cleaned_full_type_ov'))
        if self.is_event() or self.is_relation():
            if unspecified(self.get('entry').get('subtype')):
                cleaned_full_type = '{}.Unspecified'.format(cleaned_full_type)
        return cleaned_full_type

    def get_cleaned_full_type_ov(self):
        entry = self.get('entry')
        if unspecified(entry.get('type')):
            return
        full_type = entry.get('type')
        if not unspecified(entry.get('subtype')):
            full_type = '{}.{}'.format(entry.get('type'), entry.get('subtype'))
        if not unspecified(entry.get('subtype')) and not unspecified(entry.get('subsubtype')):
            full_type = '{}.{}.{}'.format(entry.get('type'), entry.get('subtype'), entry.get('subsubtype'))
        return full_type
        
    def get_full_type(self):
        return self.get('cleaned_full_type')

    def get_id(self):
        return self.get('entry').get('eventmention_id') or self.get('entry').get('relationmention_id') or self.get('entry').get('argmention_id')

    def get_informative_justification_spans(self):
        informative_justification_spans = {} 
        for span in self.get('document_spans').values():
            document_id = span.get('document_id')
            if document_id not in informative_justification_spans:
                informative_justification_spans[document_id] = span
            else:
                informative_justification_spans[document_id] = self.get('preferred_span', informative_justification_spans[document_id], span)
        return informative_justification_spans

    def get_document_id(self):
        return self.get('entry').get('root_uid')
        
    def get_document_element_id(self):
        return self.get('entry').get('child_uid')
    
    def get_document_element_modality(self):
        return self.get('document_mappings').get('document_elements').get(self.get('document_element_id')).get('modality')

    def get_keyframe_id(self):
        return self.get('entry').get('keyframe_id')

    def get_preferred_span(self, span1, span2):
        if self.get('node_metatype') == 'entity':
            if span1.get('span_type') == 'keyframe':
                return span1
            elif span2.get('span_type') == 'keyframe':
                return span2
        elif self.get('node_metatype') == 'event' or self.get('node_metatype') == 'relation':
            if span1.get('span_type') == 'picture_channel_video' or span1.get('span_type') == 'sound_channel_video':
                return span1
            elif span2.get('span_type') == 'picture_channel_video' or span2.get('span_type') == 'sound_channel_video':
                return span2
        return

    def is_event(self):
        return self.get('entry').get('eventmention_id') is not None
    
    def is_entity(self):
        return self.get('entry').get('argmention_id') is not None
    
    def is_relation(self):
        return self.get('entry').get('relationmention_id') is not None
    
    def load_node_metatype(self):
        node_metatype = None
        if self.is_event():
            node_metatype = 'event'
        elif self.is_relation():
            node_metatype = 'relation'
        elif self.is_entity():
            node_metatype = 'entity'
        self.node_metatype = node_metatype

    def load_document_spans(self):
        entry = self.get('entry')
        pattern = re.compile('^(\d+),(\d+),(\d+),(\d+)$')
        match = pattern.match(entry.get('mediamention_coordinates'))
        if self.get('text_boundaries').exists(self.get('document_element_id')):
            if is_number(entry.get('textoffset_startchar')) and is_number(entry.get('textoffset_endchar')):
                document_span = DocumentSpan(self.get('logger'),
                                             self.get('document_id'),
                                             self.get('document_element_id'),
                                             None,
                                             self.get('document_element_modality'),
                                             'text',
                                             entry.get('textoffset_startchar'),
                                             0,
                                             entry.get('textoffset_endchar'),
                                             0,
                                             entry.get('where'))
                self.document_spans[document_span.__str__()] = document_span
        elif self.get('image_boundaries').exists(self.get('document_element_id')):
            if match:
                start_x, start_y, end_x, end_y = map(lambda i : match.group(i), range(1, 5))
                document_span = DocumentSpan(self.get('logger'),
                                             self.get('document_id'),
                                             self.get('document_element_id'),
                                             None,
                                             self.get('document_element_modality'),
                                             'image',
                                             start_x,
                                             start_y,
                                             end_x,
                                             end_y,
                                             entry.get('where'))
                self.document_spans[document_span.__str__()] = document_span
        elif self.get('video_boundaries').exists(self.get('document_element_id')):
            # video is the only modality that allow at most two spans from a single entry in the mentions
            # file being read.
            #
            # if the mention has keyframe and bounding box information, put these into document spans
            if self.get('keyframe_boundaries').exists(self.get('keyframe_id')):
                if match:
                    start_x, start_y, end_x, end_y = map(lambda i : match.group(i), range(1, 5))
                    document_span = DocumentSpan(self.get('logger'),
                                                 self.get('document_id'),
                                                 self.get('document_element_id'),
                                                 self.get('keyframe_id'),
                                                 self.get('document_element_modality'),
                                                 'keyframe',
                                                 start_x,
                                                 start_y,
                                                 end_x,
                                                 end_y,
                                                 entry.get('where'))
                    self.document_spans[document_span.__str__()] = document_span

            # if the mention has start and end times, put these into document spans as well, if desired
            if self.load_video_time_offsets_flag and is_number(entry.get('mediamention_starttime')) and is_number(entry.get('mediamention_endtime')):
                document_span = DocumentSpan(self.get('logger'),
                                             self.get('document_id'),
                                             self.get('document_element_id'),
                                             None,
                                             self.get('document_element_modality'),
                                             entry.get('mediamention_signaltype'),
                                             entry.get('mediamention_starttime'),
                                             0,
                                             entry.get('mediamention_endtime'),
                                             0,
                                             entry.get('where'))
                self.document_spans[document_span.__str__()] = document_span
        elif self.get('audio_boundaries').exists(self.get('document_element_id')):
            if is_number(entry.get('mediamention_starttime')) and is_number(entry.get('mediamention_endtime')):
                document_span = DocumentSpan(self.get('logger'),
                                             self.get('document_id'),
                                             self.get('document_element_id'),
                                             None,
                                             'audio',
                                             entry.get('mediamention_signaltype'),
                                             entry.get('mediamention_starttime'),
                                             0,
                                             entry.get('mediamention_endtime'),
                                             0,
                                             entry.get('where'))

        if len(self.document_spans) == 0:
            self.get('logger').record_event('NO_SPAN_TYPE', self.get('id'), entry.get('where'))
    
    def add_node(self, node):
        self.nodes[node.get('id')] = node