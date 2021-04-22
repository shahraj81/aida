"""
AIDA Scorer class.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.object import Object
from aida.container import Container

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

    def aggregate_scores(self, scores, score_class):
        aggregates = {}
        for score in scores.values():
            languages = [score.get('language'), 'ALL']
            metatypes = [score.get('metatype'), 'ALL']
            for language in languages:
                for metatype in metatypes:
                    group_by = language + ',' + metatype
                    if group_by not in aggregates:
                        aggregates[group_by] = score_class(self.get('logger'),
                                                           aggregate=True,
                                                           language=language,
                                                           metatype=metatype,
                                                           run_id=self.get('run_id'),
                                                           summary=True,
                                                           elements=Container(self.get('logger')))
                    aggregate_scores = aggregates[group_by]
                    aggregate_scores.get('elements').add(score)
        for score in sorted(aggregates.values(), key=self.order):
            scores.add(score)

    def order(self, k):
        language, metatype = k.get('language'), k.get('metatype')
        metatype = '_ALL' if metatype == 'ALL' else metatype
        language = '_ALL' if language == 'ALL' else language
        return '{language}:{metatype}'.format(metatype=metatype, language=language)

    def print_scores(self, filename, separator):
        scores = self.get('scores')
        scores.set('separator', separator)
        fh = open(filename, 'w')
        fh.write(scores.__str__())
        fh.close()