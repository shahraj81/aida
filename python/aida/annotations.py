"""
AIDA annotations to be used as ground truth
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "27 December 2019"

from aida.file_handler import FileHandler
from aida.object import Object
from aida.mention import Mention
from aida.node import Node
from aida.slot import Slot
from aida.container import Container
import os

class Annotations(Object):
    """
    The object of this module holds AIDA annotations.
    
    This module loads annotations and provides access to entities, relations and events collected
    as part of the annotation process. 
    """

    load_file_types = {
            'mentions': { 
                'order': 1, 
                'types': ['arg_mentions', 'evt_mentions', 'rel_mentions']
                },
            'slots': { 
                'order': 2,
                'types': ['evt_slots', 'rel_slots']
                },
            'linking': {
                'order': 3,
                'types': ['kb_linking']
                } 
        }

    def __init__(self, logger, slot_mappings, document_mappings, text_boundaries, image_boundaries, video_boundaries, keyframe_boundaries, type_mappings, annotations_dir, load_topic_ids=None, load_video_time_offsets_flag=True):
        """
        Initialize the Annotations.

        Arguments:
            logger (aida.Logger)
            slot_mappings (aida.SlotMappings)
            document_mappings (aida.DocumentMappings)
            text_boundaries (aida.TextBoundaries)
            image_boundaries (aida.ImageBoundaries)
            video_boundaries (aida.VideoBoundaries)
            keyframe_boundaries (aida.KeyFrameBoundaries)
            type_mappings (aida.Container)
            annotations_dir (str):
                The path to the annotations directory as received from LDC.
            load_topic_ids (None or list):
                Specify the topic IDs to load, or set it to None in order to load all the topics.
            load_video_time_offsets_flag (bool):
                Set it to True in order to load video time offsets, False otherwise.
        """
        super().__init__(logger)
        self.logger = logger
        self.annotations_dir = annotations_dir
        self.document_mappings = document_mappings
        self.text_boundaries = text_boundaries
        self.image_boundaries = image_boundaries
        self.video_boundaries = video_boundaries
        self.keyframe_boundaries = keyframe_boundaries
        self.type_mappings = type_mappings
        self.load_topic_ids = load_topic_ids
        if self.load_topic_ids is None:
            self.load_topic_ids = list(os.listdir(annotations_dir + "/data"))
        self.slot_mappings = slot_mappings
        self.load_video_time_offsets_flag = load_video_time_offsets_flag
        self.mentions = {}
        self.nodes = {}
        self.subject_nodes = {}
        self.slots = Container(logger)
        self.load_annotations()
    
    def process_arg_mentions(self, filename):
        """
        Processes the argument mentions.
        """
        self.process_mentions(filename, 'argmention_id')

    def process_evt_mentions(self, filename):
        """
        Processes the event mentions.
        """
        self.process_mentions(filename, 'eventmention_id')

    def process_rel_mentions(self, filename):
        """
        Processes the relation mentions.
        """
        self.process_mentions(filename, 'relationmention_id')

    def process_mentions(self, filename, key_fieldname):
        """
        Processes the mentions from the file specified using the argument 'filename',
        and store the mentions into the mentions dictionary using the key taken
        from the entry using the argument 'key_fieldname'.
        """
        for entry in FileHandler(self.logger, filename):
            key = entry.get(key_fieldname)
            if self.mentions.get(key, None) is None:
                mention = Mention(self.logger, self.document_mappings, self.text_boundaries, self.image_boundaries, self.video_boundaries, self.keyframe_boundaries, self.type_mappings, self.load_video_time_offsets_flag, entry)
                if len(mention.get('document_spans')) > 0:
                    self.mentions[key] = mention
                else:
                    self.record_event('MISSING_SPAN_FOR_MENTION', key, entry.get('where'))
            else:
                self.record_event('DUPLICATE_VALUE_IN_COLUMN', key, key_fieldname, entry.get('where'))

    def process_evt_slots(self, filename):
        """
        Processes event slots.
        """
        self.process_slots(filename, 'eventmention_id')

    def process_rel_slots(self, filename):
        """
        Processes relation slots.
        """
        self.process_slots(filename, 'relationmention_id')
    
    def process_slots(self, filename, subjectmentionid_fieldname):
        """
        Processes the slots from the file specified using the argument 'filename',
        and store the slots into the slots container.

        Note that this method is called for both the relation slots, and event slots,
        and the key field name, i.e. the subject mention ID fieldname, is different.
        It is called 'relationmention_id' for relations, and 'eventmention_id' for
        events. This is why we use the parameter subjectmentionid_fieldname to choose
        between the two depending on where we are processing relations or events.
        """
        for entry in FileHandler(self.logger, filename):
            subjectmention_id = entry.get(subjectmentionid_fieldname)
            slot_code = entry.get('slot_type')
            slot_type = self.get('slot_mappings').get('code_to_type', slot_code)
            argmention_id = entry.get('argmention_id')
            subject = self.get('mentions').get(subjectmention_id, None)
            argument = self.get('mentions').get(argmention_id, None)
            attribute = entry.get('attribute')
            if subject is None:
                self.get('logger').record_event('MISSING_ITEM_WITH_KEY', 'Mention', subjectmention_id, entry.get('where'))
                continue
            if argument is None:
                self.get('logger').record_event('MISSING_ITEM_WITH_KEY', 'Mention', argmention_id, entry.get('where'))
                continue
            slot = Slot(self.logger, subject, slot_code, slot_type, argument, attribute, entry.get('where'))
            subject.add_slot(slot)
            argument.add_slot(slot)
            self.get('slots').add_member(slot)

    def process_kb_linking(self, filename):
        """
        Processes the KB linking information.
        """
        for entry in FileHandler(self.logger, filename):
            kb_id_or_kb_ids = entry.get('kb_id')
            mention_id = entry.get('mention_id')
            mention = self.get('mentions').get(mention_id, None)
            if mention is None:
                self.record_event('MISSING_ITEM_WITH_KEY', 'Mention', mention_id, entry.get('where'))
                continue
            node_metatype = mention.get('node_metatype')
            for kb_id in kb_id_or_kb_ids.split('|'):
                node = self.get('nodes').get(kb_id, None)
                if node is None:
                    node = Node(self.logger, kb_id, node_metatype, [mention])
                    self.nodes[kb_id] = node
                else:
                    node.add_mention(mention)
                mention.add_node(node)
        
    def load_annotations(self):
        """
        Loads the annotations.
        """
        for topic_id in self.load_topic_ids:
            for file_type_class in sorted(self.load_file_types, key=lambda x: self.load_file_types[x]['order']):
                for file_type in self.load_file_types[file_type_class]['types']:
                    method_name = "process_{}".format(file_type)
                    method = self.get_method(method_name)
                    if method is None:
                        self.record_event("UNDEFINED_METHOD", method_name, self.get_code_location())
                    filename = "{}/data/{}/{}_{}.tab".format(self.annotations_dir, topic_id, topic_id, file_type)
                    method(filename)