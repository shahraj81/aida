"""
The class to hold ontology types.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "11 August 2020"

from aida.file_handler import FileHandler
from aida.container import Container
from aida.object import Object

class OntologyTypeMappings(Object):
    """
    The class to hold ontology types.
    """

    def __init__(self, logger, filename):
        super().__init__(logger)
        self.logger = logger
        self.filename = filename
        self.containers = {
            'Entity': Container(logger),
            'Relation': Container(logger),
            'Event': Container(logger)
            } 
        self.load_data()

    def type_to_metatype(self, full_type):
        retVal = None
        for metatype in self.get('containers'):
            if self.has(metatype, full_type):
                if retVal is not None:
                    self.record_event('DEFAULT_CRITICAL_ERROR', 'Found multiple values for metatype: {},{}'.format(metatype, retVal))
                retVal = metatype
        if retVal is None:
            self.record_event('DEFAULT_CRITICAL_ERROR', 'Unknown metatype corresponding to type \'{}\''.format(full_type))
        return retVal

    def load_data(self):
        fh = FileHandler(self.logger, self.filename)
        for entry in fh.get('entries'):
            metatype = entry.get('metatype')
            container = self.get('containers').get(metatype)
            container.add(key=entry.get('ontology_id'), value=entry.get('full_type'))

    def has(self, metatype, full_type):
        return full_type in self.get('containers').get(metatype).values()