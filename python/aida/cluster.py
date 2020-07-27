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
from aida.utility import trim_cv, spanstring_to_object

class Cluster(Object):

    def __init__(self, logger, ID):
        super().__init__(logger)
        self.ID = ID
        self.types = Container(logger)
        self.mentions = Container(logger)
        self.metatype = None

    def add(self, entry):
        self.add_metatype(entry.get('?metatype'), entry.get('where'))
        self.add_type(entry.get('?type'))
        self.add_mention(entry.get('?mention_span'),
                         trim_cv(entry.get('?t_cv')),
                         trim_cv(entry.get('?cm_cv')),
                         trim_cv(entry.get('?j_cv')),
                         entry.get('where'))

    def add_metatype(self, metatype, where):
        if self.get('metatype') is None:
            self.set('metatype', metatype)
        if metatype != self.get('metatype'):
            self.get('logger').record_event('MISMATCHED_METATYPE', metatype, self.get('metatype'), where)

    def add_type(self, cluster_type):
        self.get('types').add(cluster_type, cluster_type)

    def add_mention(self, span_string, t_cv, cm_cv, j_cv, where):
        logger = self.get('logger')
        mention = Object(logger)
        mention.set('ID', span_string)
        mention.set('span_string', span_string)
        mention.set('t_cv', t_cv)
        mention.set('cm_cv', cm_cv)
        mention.set('j_cv', j_cv)
        mention.set('span', spanstring_to_object(logger, span_string, where))
        self.get('mentions').add(key=mention.get('ID'), value=mention)

    def __str__(self, *args, **kwargs):
        return self.get('ID')