"""
AIDA class containing self-similarities between gold clusters, and self-similarities between system clusters.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "17 August 2020"

from aida.container import Container
from aida.file_handler import FileHandler
from aida.object import Object

import os

class ClusterSelfSimilarities(Object):
    """
    AIDA class containing self-similarities between gold clusters, and self-similarities between system clusters.
    """
    def __init__(self, logger, similarities_directory):
        super().__init__(logger)
        self.directory = similarities_directory
        self.cluster_to_metatype = Container(logger)
        self.gold = Container(logger)
        self.system = Container(logger)
        self.load()

    def load(self):
        logger = self.get('logger')
        for filename in sorted(os.listdir(self.get('directory')), key=str):
            filename_including_path = '{}/{}'.format(self.get('directory'), filename)
            document_id = filename.replace('.tab', '')
            for entry in FileHandler(logger, filename_including_path):
                metatype = entry.get('metatype')
                system_or_gold1 = entry.get('system_or_gold1')
                system_or_gold2 = entry.get('system_or_gold2')
                cluster1 = entry.get('cluster1')
                cluster2 = entry.get('cluster2')
                similarity = entry.get('similarity')
                if similarity == 0 or system_or_gold1 != system_or_gold2 or cluster1 != cluster2: continue
                self.get('cluster_to_metatype').add(key='{}:{}'.format(system_or_gold1.upper(), cluster1), value=metatype)
                self.get('cluster_to_metatype').add(key='{}:{}'.format(system_or_gold1.upper(), cluster1), value=metatype)
                self.get(system_or_gold).get(document_id, default=Container(logger)).add(key=cluster1, value=similarity)