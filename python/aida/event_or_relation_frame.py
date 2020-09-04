"""
AIDA edge class.

This class supports the alignment of edges as needed for scoring.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 July 2020"

from aida.object import Object

class EventOrRelationFrame(Object):

    def __init__(self, logger, ID, where):
        super().__init__(logger)
        self.ID = ID
        self.metatype = None
        self.role_fillers = {}
        self.types = {}
        self.where = where

    def get_number_of_fillers(self):
        number_of_fillers = 0
        for rolename in self.get('role_fillers'):
            number_of_fillers += len(self.get('role_fillers').get(rolename))
        return number_of_fillers

    def get_top_level_types(self):
        top_level_types = {}
        num_levels_by_metatype = {'Event': 2, 'Relation': 2}
        num_levels = num_levels_by_metatype[self.get('metatype')]
        for cluster_type in self.get('types'):
            elements = []
            for element in cluster_type.split('.'):
                if num_levels > 0:
                    elements.append(element)
                    num_levels -= 1
            top_level_types['.'.join(elements)] = 1
        return list(top_level_types.keys())

    def is_alignable_relation(self):
        """
        Event or relation frame is alignable if and only if it is both
        (1) a relation, and (2) has two fillers.
        """
        if self.get('metatype') != 'Relation': return False
        number_of_fillers = self.get('number_of_fillers')
        if number_of_fillers != 2:
            self.record_event('UNEXPECTED_NUM_OF_REL_FILLERS', self.get('ID'), number_of_fillers, self.get('where'))
            return False
        return True

    def update(self, entry):
        schema_name = entry.get('schema').get('name')
        method_name = 'update_{}'.format(schema_name)
        method = self.get_method(method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name, self.get_code_location())
        method(entry)

    def update_AIDA_PHASE2_TASK1_AM_RESPONSE(self, entry):
        event_or_relation_type, rolename = entry.get('?predicate').split('_')
        if self.get('metatype') is None:
            self.set('metatype', entry.get('?metatype'))
        if self.get('metatype') != entry.get('?metatype'):
            self.record_event('METATYPE_MISMATCH', self.get('ID'), self.get('metatype'), entry.get('?metatype'), entry.get('where'))
        self.get('types')[event_or_relation_type] = 1
        filler = Object(self.get('logger'))
        filler_cluster_id = entry.get('?object')
        filler.set('predicate', entry.get('predicate'))
        filler.set('filler_cluster_id', filler_cluster_id)
        filler.set('predicate_justification', entry.get('?predicate_justification'))
        filler.set('argument_assertion_confidence', entry.get('?argument_assertion_confidence'))
        filler.set('predicate_justification_confidence', entry.get('?predicate_justification_confidence'))
        filler.set('where', entry.get('where'))
        if rolename not in self.get('role_fillers'):
            self.get('role_fillers')[rolename] = {}
        if filler_cluster_id not in self.get('role_fillers')[rolename]:
            self.get('role_fillers')[rolename][filler_cluster_id] = []
        self.get('role_fillers')[rolename][filler_cluster_id].append(filler)

    def update_AIDA_PHASE2_TASK1_TM_RESPONSE(self, entry):
        # nothing to update
        pass