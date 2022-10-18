"""
Set of TA3 queries for AIDA.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 February 2022"

from aida.object import Object
from aida.file_handler import FileHandler
from aida.file_header import FileHeader

import os

class TA3QuerySet(Object):
    """
    Set of TA3 queries for AIDA.
    """

    def __init__(self, logger, directory):
        super().__init__(logger)
        self.directory = directory
        self.conditions = {}
        self.load()

    def get_claim_template(self, condition, query_id):
        return self.get('conditions').get(condition).get('topics').get(query_id)[0].get('claim_template')

    def get_topic(self, condition, query_id):
        return self.get('conditions').get(condition).get('topics').get(query_id)[0].get('topic')

    def parse_topics(self, condition, topics_file):
        logger = self.get('logger')
        header_columns = {
            'Condition5': ['topic_id', 'topic', 'subtopic', 'claim_template'],
            'Condition6': ['topic_id', 'topic', 'subtopic', 'claim_template'],
            'Condition7': ['topic_id', 'topic']
            }
        header = FileHeader(logger, '\t'.join(header_columns.get(condition)))
        topics = {}
        for entry in FileHandler(logger, topics_file, header=header):
            topics.setdefault(entry.get('topic_id'), []).append(entry)
        return topics

    def load(self):
        def parse_ttl(filename):
            topic = None
            subtopic = None
            with open(filename) as fh:
                for line in fh.readlines():
                    elements = line.split()
                    if len(elements) < 2: continue
                    if elements[0] == 'aida:topic':
                        topic = ' '.join(elements[1:-1])
                    if elements[0] == 'aida:subtopic':
                        subtopic = ' '.join(elements[1:-1])
                    if elements[0] == 'aida:naturalLanguageDescription':
                        naturalLanguageDescription = ' '.join(elements[1:-1])
            return [t.replace('"','') for t in [topic, subtopic, naturalLanguageDescription]]
        conditions = self.get('conditions')
        directory = self.get('directory')
        for item in os.listdir(directory):
            if item.startswith('.'): continue
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                conditions[item] = {
                    'name': item,
                    'directory': item_path,
                    'query_claim_frames': None,
                    'topics_file': None,
                    'topics': None
                    }
                for subitem in os.listdir(item_path):
                    subitem_path = os.path.join(item_path, subitem)
                    if os.path.isfile(subitem_path) and subitem_path.endswith('topics.tsv'):
                        conditions.get(item)['topics_file'] = subitem_path
                        conditions.get(item)['topics'] = self.parse_topics(item, subitem_path)
                    elif os.path.isdir(subitem_path) and subitem == 'Query_Claim_Frames':
                        conditions.get(item)['query_claim_frames'] = {}
                        for subsubitem in os.listdir(subitem_path):
                            subsubitem_path = os.path.join(subitem_path, subsubitem)
                            if os.path.isfile(subsubitem_path) and subsubitem.endswith('.ttl'):
                                claim_id = subsubitem.replace('.ttl', '')
                                topic, subtopic, naturalLanguageDescription = parse_ttl(subsubitem_path)
                                conditions.get(item).get('query_claim_frames')[claim_id] = {
                                    'topic': topic,
                                    'subtopic': subtopic,
                                    'naturalLanguageDescription': naturalLanguageDescription
                                    }
            # add topic id to query claim frames
            topics = conditions.get(item).get('topics')
            query_claim_frames = conditions.get(item).get('query_claim_frames')
            if query_claim_frames is None: continue
            for topic_id in topics:
                for claim_id in query_claim_frames:
                    claim_frame_struct = query_claim_frames.get(claim_id)
                    for entry in topics.get(topic_id):
                        if claim_frame_struct.get('topic') == entry.get('topic'):
                            if claim_frame_struct.get('subtopic') == entry.get('subtopic'):
                                claim_frame_struct['topic_id'] = topic_id
