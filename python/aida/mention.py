"""
The class representing a mention.
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
    The class representing a mention.
    """

    def __init__(self, logger, document_mappings, text_boundaries, image_boundaries, video_boundaries, keyframe_boundaries, type_mappings, load_video_time_offsets_flag, entry):
        """
        Initialize a mention instance.

        Parameters:
            logger (aida.Logger)
            document_mappings (aida.DocumentMappings)
            text_boundaries (aida.TextBoundaries)
            image_boundaries (aida.ImageBoundaries)
            video_boundaries (aida.VideoBoundaries)
            keyframe_boundaries (aida.KeyFrameBoundaries)
            type_mappings (aida.Container)
            load_video_time_offsets_flag (bool)
            entry (aida.Entry)
        """
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
        # the slots in which the mention participates
        self.slots = {}
        # the document spans included in this mention
        self.document_spans = {}
        # set the span of text, or image bounding box of the 
        # mention
        self.load_document_spans()
        # set the 'node_metatype' (i.e. ENTITY, RELATION, or 
        # ENTITY) of the nodes referred to by this mention
        self.load_node_metatype()

    def get_cleaned_full_type(self):
        """
        Gets the cleaned full type of the mention.

        This method first concatenates the type, subtype, and subsubtype,
        removing any trailing undefined types, and then look up the proper-cased
        full type in type mappings container.

        Note that the type mappings container maps the output value type to
        proper-typed types.
        """
        entry = self.get('entry')
        cleaned_full_type = self.get('cleaned_full_type_ov')
        if self.is_event() or self.is_relation():
            if unspecified(self.get('entry').get('subtype')):
                if unspecified(self.get('entry').get('subsubtype')):
                    cleaned_full_type = '{}.unspecified'.format(entry.get('type'))
                else:
                    cleaned_full_type = '{}.unspecified.{}'.format(entry.get('type'), entry.get('subsubtype'))
        propercased_cleaned_full_type = self.type_mappings.get(cleaned_full_type, None)
        retval = propercased_cleaned_full_type if propercased_cleaned_full_type is not None else cleaned_full_type
        return retval

    def get_cleaned_full_type_ov(self):
        """
        Gets the cleaned Full Type OV.

        Note that OV is the type written in lower case descriptive type name as it came from LDC; OV values
        are not the proper cased types used in the AIF.
        """
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
        """
        Gets the full type of the mention.

        At this point, this method simply returns the output of the get_cleaned_full_type method.
        """
        return self.get('cleaned_full_type')

    def get_ID(self):
        """
        Gets the ID of the mention.

        The ID returned is the value of the following field taken from the entry:
            argmention_id -- for entity mention
            relationmention_id -- for relation mention
            eventmention_id -- for event mention
        """
        return self.get('entry').get('eventmention_id') or self.get('entry').get('relationmention_id') or self.get('entry').get('argmention_id')

    def get_informative_justification_spans(self):
        """
        Gets the informative justification spans of this mention.

        The return value is a dictionary object that has one informative justification
        span per document.
        """
        informative_justification_spans = {} 
        for span in self.get('document_spans').values():
            document_id = span.get('document_id')
            if document_id not in informative_justification_spans:
                informative_justification_spans[document_id] = span
            else:
                informative_justification_spans[document_id] = self.get('preferred_span', informative_justification_spans[document_id], span)
        return informative_justification_spans

    def get_document_id(self):
        """
        Gets the document ID from which the mention was drawn.
        """
        return self.get('entry').get('root_uid')

    def get_document_element_id(self):
        """
        Gets the document element ID from which the mention was drawn.
        """
        return self.get('entry').get('child_uid')

    def get_document_element_modality(self):
        """
        Gets modality of the document element ID from which the mention was drawn.
        """
        return self.get('document_mappings').get('document_elements').get(self.get('document_element_id')).get('modality')

    def get_keyframe_id(self):
        """
        Gets keyframe ID from which the mention was drawn.
        """
        return self.get('entry').get('keyframe_id')

    def get_preferred_span(self, span1, span2):
        """
        Out of the two spans provided as argument, pick one that should be preferred over the other as the candidate of informative justification.
        """
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
        """
        Returns True if the mention is a mention of an event, False otherwise.
        """
        return self.get('entry').get('eventmention_id') is not None

    def is_entity(self):
        """
        Returns True if the mention is a mention of an entity, False otherwise.
        """
        return self.get('entry').get('argmention_id') is not None

    def is_relation(self):
        """
        Returns True if the mention is a mention of a relation, False otherwise.
        """
        return self.get('entry').get('relationmention_id') is not None

    def is_negated(self):
        """
        Returns True if the mention is a negated, False otherwise.
        """
        attributes = self.get('entry').get('attribute')
        return attributes is not None and 'not' in attributes.split(',')

    def load_node_metatype(self):
        """
        Determines and sets the metatype of the node based on this mention.
        """
        node_metatype = None
        if self.is_event():
            node_metatype = 'event'
        elif self.is_relation():
            node_metatype = 'relation'
        elif self.is_entity():
            node_metatype = 'entity'
        self.node_metatype = node_metatype

    def load_document_spans(self):
        """
        Loads the document spans corresponding to the mention.
        """
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
                self.document_spans[document_span.__str__()] = document_span
        if len(self.document_spans) == 0:
            self.get('logger').record_event('MISSING_ITEM_WITH_KEY', 'Span type for mention', self.get('ID'), entry.get('where'))

    def add_node(self, node):
        """
        Adds the node to this mention.

        By doing so we are implying that this instance of the Mention class is a mention of the node
        which is passed as the only argument to this method.
        """
        self.nodes[node.get('ID')] = node

    def add_slot(self, slot):
        """
        Adds the slot to the mention.
        """
        if slot.get('slot_type') not in self.get('slots'):
            self.get('slots')[slot.get('slot_type')] = []
        self.get('slots').get(slot.get('slot_type')).append(slot)