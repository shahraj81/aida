"""
AIDA class containing alignment between gold and system clusters.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "17 August 2020"

from aida.container import Container
from aida.file_handler import FileHandler
from aida.object import Object

import os

class ClusterAlignment(Object):
    """
    AIDA class containing alignment between gold and system clusters.
    """
    def __init__(self, logger, alignment_directory):
        super().__init__(logger)
        self.directory = alignment_directory
        self.cluster_to_metatype = Container(logger)
        self.system_to_gold = Container(logger)
        self.gold_to_system = Container(logger)
        self.load()

    def load(self):
        logger = self.get('logger')
        for filename in sorted(os.listdir(self.get('directory')), key=str):
            filename_including_path = '{}/{}'.format(self.get('directory'), filename)
            for entry in FileHandler(logger, filename_including_path):
                metatype = entry.get('metatype')
                system_cluster = entry.get('system_cluster')
                gold_cluster = entry.get('gold_cluster')
                similarity = entry.get('similarity')
                self.get('cluster_to_metatype').add(key='GOLD:{}'.format(gold_cluster), value=metatype)
                self.get('cluster_to_metatype').add(key='SYSTEM:{}'.format(system_cluster), value=metatype)
                self.get('system_to_gold').add(key=system_cluster, value={'aligned_to': gold_cluster, 'aligned_similarity': similarity})
                self.get('gold_to_system').add(key=gold_cluster, value={'aligned_to': system_cluster, 'aligned_similarity': similarity})