"""
AIDA class containing alignment between gold and system mention for a pair of aligned gold and system mentions.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "13 September 2022"

from aida.container import Container
from aida.file_handler import FileHandler
from aida.object import Object
from tqdm import tqdm
import os

class MentionAlignment(Container):
    """
    AIDA class containing alignment between gold and system mention for a pair of aligned gold and system mentions.
    """
    def __init__(self, logger, alignment_directory):
        super().__init__(logger)
        self.directory = alignment_directory
        self.load()

    def load(self):
        logger = self.get('logger')
        for filename in tqdm(sorted(os.listdir(self.get('directory')), key=str), desc='loading mention alignment'):
            filename_including_path = '{}/{}'.format(self.get('directory'), filename)
            document_id = filename.replace('.tab', '')
            for entry in FileHandler(logger, filename_including_path):
                system_cluster = entry.get('system_cluster')
                gold_cluster = entry.get('gold_cluster')
                system_mention = entry.get('system_mention')
                gold_mention = entry.get('gold_mention')
                similarity = entry.get('similarity')
                document_alignment = self.get(document_id, default=Container(logger))
                document_system_cluster_alignment = document_alignment.get(system_cluster, default=Container(logger))
                document_system_cluster_alignment.set('aligned_to', gold_cluster)
                mention_alignment = document_system_cluster_alignment.get(system_mention, default=Object(logger))
                mention_alignment.set('aligned_to', gold_mention)
                mention_alignment.set('aligned_similarity', similarity)