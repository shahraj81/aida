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
        self.system_to_gold = Container(logger)
        self.gold_to_system = Container(logger)
        self.load()

    def load(self):
        logger = self.get('logger')
        for filename in sorted(os.listdir(self.get('directory')), key=str):
            filename_including_path = '{}/{}'.format(self.get('directory'), filename)
            document_id = filename.replace('.tab', '')
            for entry in FileHandler(logger, filename_including_path):
                system_cluster = entry.get('system_cluster')
                gold_cluster = entry.get('gold_cluster')
                similarity = entry.get('similarity')
                document_system_to_gold = self.get('system_to_gold').get(document_id, default=Container(logger))
                document_gold_to_system = self.get('gold_to_system').get(document_id, default=Container(logger))
                document_system_to_gold.add(key=system_cluster, value={'aligned_to': gold_cluster, 'aligned_similarity': similarity})
                document_gold_to_system.add(key=gold_cluster, value={'aligned_to': system_cluster, 'aligned_similarity': similarity})