"""
AIDA Scorer class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.object import Object
from aida.confidence_intervals import ConfidenceIntervals

class Scorer(Object):
    """
    AIDA Scorer class.
    """

    def __init__(self, logger, separator=None, **kwargs):
        super().__init__(logger)
        self.separator = separator
        for key in kwargs:
            self.set(key, kwargs[key])
        self.separator = separator
        self.score_responses()
        self.compute_confidence_intervals()

    def compute_confidence_intervals(self):
        self.set('confidence_intervals', ConfidenceIntervals(self.get('logger'), self.get('run_id'), self.__class__.__name__, self.get('scores')))

    def get_cluster(self, system_or_gold, document_id, cluster_id):
        cluster = None
        if document_id in self.get('{}_responses'.format(system_or_gold)).get('document_clusters'):
            if cluster_id in self.get('{}_responses'.format(system_or_gold)).get('document_clusters').get(document_id):
                cluster = self.get('{}_responses'.format(system_or_gold)).get('document_clusters').get(document_id).get(cluster_id)
        return cluster

    def get_frame(self, system_or_gold, document_id, cluster_id):
        frame = None
        if document_id in self.get('{}_responses'.format(system_or_gold)).get('document_frames'):
            if cluster_id in self.get('{}_responses'.format(system_or_gold)).get('document_frames').get(document_id):
                frame = self.get('{}_responses'.format(system_or_gold)).get('document_frames').get(document_id).get(cluster_id)
        return frame

    def get_core_documents(self):
        return self.get('gold_responses').get('document_mappings').get('core_documents')

    def print_confidence_intervals(self, filename):
        fh = open(filename, 'w')
        fh.write(self.get('confidence_intervals').__str__())
        fh.close()

    def print_scores(self, filename):
        fh = open(filename, 'w')
        fh.write(self.__str__())
        fh.close()

    def __str__(self):
        return self.get('scores').__str__()