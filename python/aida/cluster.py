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
from aida.utility import parse_cv
from aida.span import Span
import re

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
                         parse_cv(entry.get('?t_cv')),
                         parse_cv(entry.get('?cm_cv')),
                         parse_cv(entry.get('?j_cv')))

    def add_metatype(self, metatype, where):
        if self.get('metatype') is None:
            self.set('metatype', metatype)
        if metatype != self.get('metatype'):
            self.get('logger').record_event('MISMATCHED_METATYPE', metatype, self.get('metatype'), where)

    def add_type(self, cluster_type):
        self.get('types').add(cluster_type, cluster_type)

    def add_mention(self, span_string, t_cv, cm_cv, j_cv):
        logger = self.get('logger')
        mention = Object(logger)
        mention.set('ID', span_string)
        mention.set('span_string', span_string)
        mention.set('t_cv', t_cv)
        mention.set('cm_cv', cm_cv)
        mention.set('j_cv', j_cv)
        self.get('mentions').add(key=mention.get('ID'), value=mention)
        
        pattern = re.compile('^(.*?):(.*?):\((\d+),(\d+)\)-\((\d+),(\d+)\)$')
        match = pattern.match(span_string)
        if match:
            document_id = match.group(1)
            document_eleemnt_id = match.group(2)
            span = Span(logger, match.group(3), match.group(4), match.group(5), match.group(6))
            mention.set('document_id', document_id)
            mention.set('document_element_id', document_eleemnt_id)
            mention.set('span', span)

    def __str__(self, *args, **kwargs):
        return self.get('ID')