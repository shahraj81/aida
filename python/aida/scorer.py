"""
AIDA Scorer class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.object import Object

class Scorer(Object):
    """
    AIDA Scorer class.
    """

    def __init__(self, logger, **kwargs):
        super().__init__(logger)
        for key in kwargs:
            self.set(key, kwargs[key])
        self.score_responses()

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

    def print_scores(self, filename, separator):
        scores = self.get('scores')
        scores.set('separator', separator)
        fh = open(filename, 'w')
        fh.write(scores.__str__())
        fh.close()