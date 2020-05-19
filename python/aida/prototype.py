"""
The class representing the prototype of a Node.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "7th May 2020"

from aida.object import Object

class Prototype(Object):
    """
    The class representing the prototype of a Node.
    """

    def __init__(self, node):
        """
        Initialize the Prototype.

        Parameters:
            logger (aida.Logger)
            node (aida.Node)
        """
        super().__init__(node.get('logger'))
        self.ID = 'prototype-{}'.format(node.get('name'))
        self.node = node
        self.types = {}
        self.slots = {}
        self.text_strings = {}
        self.load(node)

    def load(self, node):
        """
        Uses node to load the data needed by the Prototype.
        """
        self.informative_justification_mention_spans = node.get('informative_justification_mention_spans')
        if self.get('metatype') is None:
            self.metatype = node.get('metatype')
        elif self.get('metatype') != node.get('metatype'):
            self.get('logger').record_event('METATYPE_MISMATCH', node.get('ID'), node.get('metatype'), self.get('metatype'), node.get('where'))
        for mention in node.get('mentions').values():
            if mention.is_negated():
                self.get('logger').record_event('SKIPPING', 'mention', '{}'.format(mention.get('ID')), "because the it is negated")
                continue
            mention_type = mention.get('full_type')
            if not mention_type in self.get('types'):
                self.get('types')[mention_type] = []
            self.get('types')[mention_type].append(mention)
            for slot_type in mention.get('slots'):
                if slot_type not in self.get('slots'):
                    self.get('slots')[slot_type] = []
                for slot in mention.get('slots').get(slot_type):
                    self.get('slots').get(slot_type).append(slot)
            if mention.get('node_metatype').capitalize() == 'Entity':
                if mention.get('text_string') not in self.get('text_strings'):
                    self.get('text_strings')[mention.get('text_string')] = {mention.get('level'):1}
                else:
                    self.get('text_strings')[mention.get('text_string')][mention.get('level')] = 1
        self.add_time(node)

    def add_time(self, node):
        for mention in node.get('mentions').values():
            time_range_from_mention = mention.get('time_range')
            if time_range_from_mention is None:
                continue
            if self.get('time_range') is None:
                self.set('time_range', time_range_from_mention.get('copy'))
            else:
                time_range_from_prototype = self.get('time_range')
                if time_range_from_mention.__str__() != time_range_from_prototype.__str__():
                    mention_T1 = time_range_from_mention.get('start_time_after')
                    mention_T2 = time_range_from_mention.get('start_time_before')
                    mention_T3 = time_range_from_mention.get('end_time_after')
                    mention_T4 = time_range_from_mention.get('end_time_before')
                    prototype_T1 = time_range_from_prototype.get('start_time_after')
                    prototype_T2 = time_range_from_prototype.get('start_time_before')
                    prototype_T3 = time_range_from_prototype.get('end_time_after')
                    prototype_T4 = time_range_from_prototype.get('end_time_before')
                    if mention_T1 > prototype_T1:
                        time_range_from_prototype.set('start_time_after', mention_T1.get('copy'))
                    if mention_T2 < prototype_T2:
                        time_range_from_prototype.set('start_time_before', mention_T2.get('copy'))
                    if mention_T3 > prototype_T3:
                        time_range_from_prototype.set('end_time_after', mention_T3.get('copy'))
                    if mention_T4 < prototype_T4:
                        time_range_from_prototype.set('end_time_before', mention_T4.get('copy'))

    def get_informative_justification_spans(self):
        informative_justification_spans = {}
        for document_id in self.get('informative_justification_mention_spans'):
            mention_span = self.get('informative_justification_mention_spans')[document_id]
            informative_justification_spans[document_id] = mention_span.get('span')
        return informative_justification_spans

    def get_name(self):
        return self.get('ID')

    def get_nodes(self):
        return {self.get('node').get('ID'):self.get('node')}

    def get_node_metatype(self):
        return self.get('metatype')