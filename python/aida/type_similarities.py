"""
AIDA class containing type-similarities between system and gold clusters.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "12 September 2022"

from aida.container import Container
from aida.file_handler import FileHandler
from aida.object import Object

import os

class TypeSimilarities(Object):
    """
    AIDA class containing self-similarities between gold clusters, and self-similarities between system clusters.
    """
    def __init__(self, logger, similarities_directory):
        super().__init__(logger)
        self.directory = similarities_directory
        self.type_similarities = Container(logger)
        self.load()

    def get_document_type_similarities(self, document_id):
        return self.get('type_similarities').get(document_id)

    def get_type_similarity(self, document_id, system_cluster_id, gold_cluster_id):
        type_similarity = 0
        document_type_similarities = self.get('document_type_similarities', document_id)
        if system_cluster_id in document_type_similarities:
            if gold_cluster_id in document_type_similarities.get(system_cluster_id):
                type_similarity = document_type_similarities.get(system_cluster_id).get(gold_cluster_id)
        return type_similarity

    def load(self):
        logger = self.get('logger')
        for filename in sorted(os.listdir(self.get('directory')), key=str):
            filename_including_path = '{}/{}'.format(self.get('directory'), filename)
            document_id = filename.replace('.tab', '')
            for entry in FileHandler(logger, filename_including_path):
                system_or_gold1 = entry.get('system_or_gold1')
                system_or_gold2 = entry.get('system_or_gold2')
                if system_or_gold1 == 'system' and system_or_gold2 == 'gold':
                    system_cluster_id = entry.get('cluster1')
                    gold_cluster_id = entry.get('cluster2')
                    type_similarity = entry.get('type_similarity')
                    self.get('type_similarities').get(document_id, default=Container(logger)).get(system_cluster_id, default=Container(logger)).add(key=gold_cluster_id, value=type_similarity)