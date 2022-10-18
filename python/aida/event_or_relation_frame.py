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
        self.where = where

    def get_number_of_fillers(self):
        number_of_fillers = 0
        for rolename in self.get('role_fillers'):
            number_of_fillers += len(self.get('role_fillers').get(rolename))
        return number_of_fillers

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
        predicate = entry.get('predicate')
        if self.get('metatype') is None:
            self.set('metatype', entry.get('subject_metatype'))
        if self.get('metatype') != entry.get('subject_metatype'):
            self.record_event('METATYPE_MISMATCH', self.get('ID'), self.get('metatype'), entry.get('subject_metatype'), entry.get('where'))
        filler = Object(self.get('logger'))
        filler_cluster_id = entry.get('?object')
        filler.set('predicate', entry.get('predicate'))
        filler.set('is_assertion_negated', entry.get('is_assertion_negated'))
        filler.set('filler_cluster_id', filler_cluster_id)
        filler.set('predicate_justification', entry.get('?predicate_justification'))
        filler.set('argument_assertion_confidence', entry.get('?argument_assertion_confidence'))
        filler.set('predicate_justification_confidence', entry.get('?predicate_justification_confidence'))
        filler.set('where', entry.get('where'))
        if predicate not in self.get('role_fillers'):
            self.get('role_fillers')[predicate] = {}
        if filler_cluster_id not in self.get('role_fillers')[predicate]:
            self.get('role_fillers')[predicate][filler_cluster_id] = []
        self.get('role_fillers')[predicate][filler_cluster_id].append(filler)
        self.set('types', self.get('cluster').get('types'))