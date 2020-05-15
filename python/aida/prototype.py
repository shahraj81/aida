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
        self.ID = node.get('ID')
        self.types = {}
        self.slots = {}
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
        self.add_time(node)

    def add_time(self, node):
        for mention in node.get('mentions').values():
            time_range = mention.get('time_range')
            if time_range is None:
                continue
            if self.get('time_range') is None:
                self.set('time_range', time_range)