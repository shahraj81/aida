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

    def __init__(self, logger, ID):
        super().__init__(logger)
        self.ID = ID
        self.role_fillers = {}

    def update(self, entry):
        event_or_relation_type, rolename = entry.get('?predicate').split('_')
        if self.get('metatype') is None:
            self.set('metatype', entry.get('?metatype'))
        if self.get('event_or_relation_type') is None:
            self.set('event_or_relation_type', event_or_relation_type)
        if event_or_relation_type != self.get('event_or_relation_type'):
            self.record_event('MISMATCHED_EVENT_OR_RELATION_TYPE', event_or_relation_type, self.get('event_or_relation_type'), entry.get('where'))
        filler = Object(self.get('logger'))
        filler_cluster_id = entry.get('?object')
        filler.set('filler_cluster_id', filler_cluster_id)
        filler.set('filler_justification', entry.get('?object_inf_j_span'))
        filler.set('predicate_justification', entry.get('?ej_span'))
        filler.set('edge_cj_cv', entry.get('?edge_cj_cv'))
        filler.set('edge_cv', entry.get('?edge_cv'))
        filler.set('obj_inf_j_cv', entry.get('?obj_inf_j_cv'))
        filler.set('where', entry.get('where'))
        if rolename not in self.get('role_fillers'):
            self.get('role_fillers')[rolename] = {}
        if filler_cluster_id not in self.get('role_fillers')[rolename]:
            self.get('role_fillers')[rolename][filler_cluster_id] = []
        self.get('role_fillers')[rolename][filler_cluster_id].append(filler)
