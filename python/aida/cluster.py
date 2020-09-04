"""
AIDA Cluster class.

This class supports the alignment of clusters as needed for scoring.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 July 2020"

from aida.object import Object
from aida.container import Container
from aida.utility import get_expanded_types, trim_cv, spanstring_to_object, augment_mention_object

class Cluster(Object):

    def __init__(self, logger, document_mappings, document_boundaries, ID):
        super().__init__(logger)
        self.ID = ID
        self.document_mappings = document_mappings
        self.document_boundaries = document_boundaries
        self.types = Container(logger)
        self.mentions = Container(logger)
        self.dates = Container(logger)
        self.entries = Container(logger)
        self.metatype = None

    def get_top_level_types(self):
        top_level_types = {}
        num_levels_by_metatype = {'Entity': 1, 'Event': 2}
        num_levels = num_levels_by_metatype[self.get('metatype')]
        for cluster_type in self.get('types'):
            elements = []
            for element in cluster_type.split('.'):
                if num_levels > 0:
                    elements.append(element)
                    num_levels -= 1
            top_level_types['.'.join(elements)] = 1
        return list(top_level_types.keys())

    def get_all_expanded_types(self):
        """
        For all the types asserted for the cluster, return a union
        of corresponding expanded types.
        """
        types = []
        for cluster_type in self.get('types'):
            expanded_types = get_expanded_types(self.get('metatype'), cluster_type)
            types.extend(expanded_types)
        return list({cluster_type:1 for cluster_type in types}.keys())

    def add(self, entry):
        self.add_metatype(entry.get('?metatype'), entry.get('where'))
        self.add_type(entry.get('?type'))
        self.add_mention(entry.get('?mention_span'),
                         trim_cv(entry.get('?type_statement_confidence')),
                         trim_cv(entry.get('?cluster_membership_confidence')),
                         trim_cv(entry.get('?mention_type_justification_confidence')),
                         entry.get('where'))
        self.get('entries').add(entry)

    def add_metatype(self, metatype, where):
        if self.get('metatype') is None:
            self.set('metatype', metatype)
        if metatype != self.get('metatype'):
            self.get('logger').record_event('MULTIPLE_METATYPES', metatype, self.get('metatype'), self.get('ID'), where)

    def add_type(self, cluster_type):
        self.get('types').add(cluster_type, cluster_type)

    def add_mention(self, span_string, t_cv, cm_cv, j_cv, where):
        logger = self.get('logger')
        mention = augment_mention_object(spanstring_to_object(logger, span_string, where), self.get('document_mappings'), self.get('document_boundaries'))
        mention.set('ID', span_string)
        mention.set('span_string', span_string)
        mention.set('t_cv', t_cv)
        mention.set('cm_cv', cm_cv)
        mention.set('j_cv', j_cv)
        self.get('mentions').add(key=mention.get('ID'), value=mention)

    def is_alignable_entity_or_event(self, annotated_regions):
        return self.get('metatype') != 'Relation' and self.is_in_exhaustively_annotated_region(annotated_regions)

    def is_in_exhaustively_annotated_region(self, annotated_regions):
        for mention in self.get('mentions').values():
            if annotated_regions.contains(mention, self.get('all_expanded_types')):
                return True
        return False

    def __str__(self, *args, **kwargs):
        return self.get('ID')