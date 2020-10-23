"""
Class representing pool of task2 responses.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 October 2020"

from aida.file_handler import FileHandler
from aida.object import Object
from aida.utility import multisort, trim_cv, augment_mention_object, spanstring_to_object

import os

class Task2Pool(Object):
    """
    Class representing pool of task2 responses.
    """

    def __init__(self, logger, document_mappings, document_boundaries, runs_to_pool_file, queries_to_pool_file, previous_pools):
        super().__init__(logger)
        self.document_boundaries = document_boundaries
        self.document_mappings = document_mappings
        self.header = [
            'QUERY_ID',
            'DESCRIPTOR',
            'RESPONSE_ID',
            'MENTION_SOURCE',
            'DOCUMENT_ID',
            'MENTION_SPAN',
            'CORRECTNESS',
            'MENTION_TYPE',
            'FQEC'
            ]
        self.last_response_ids = {}
        self.previous_pool = {}
        self.previous_pool_dirs = previous_pools
        self.pool = {}
        self.runs_to_pool_file = runs_to_pool_file
        self.queries_to_pool = {}
        self.queries_to_pool_file = queries_to_pool_file
        self.load_queries_to_pool_file()
        self.load_previous_pools()

    def get_line(self, columns=None):
        if columns is None:
            return '{}\n'.format('\t'.join(self.get('header')))
        else:
            return '{}\n'.format('\t'.join([str(columns[column_name]) for column_name in self.get('header')]))

    def get_mention(self, span_string):
        logger = self.get('logger')
        return augment_mention_object(spanstring_to_object(logger, span_string, self.get('code_location')),
                                      self.get('document_mappings'),
                                      self.get('document_boundaries'))

    def get_last_response_id(self, query_id):
        last_response_ids = self.get('last_response_ids')
        if query_id not in last_response_ids:
            return 0
        return last_response_ids.get(query_id)

    def get_top_C_clusters(self, query_responses, C):
        cluster_responses = {}
        linking_confidences = {}
        clusters = []
        for linenum in query_responses:
            entry = query_responses.get(str(linenum))
            if not entry.get('valid'):
                self.record_event('EXPECTING_VALID_ENTRY', entry.get('where'))
            cluster_id = entry.get('cluster_id')
            if cluster_id not in cluster_responses:
                cluster_responses[cluster_id] = []
            cluster_responses[cluster_id].append(entry)
            linking_confidence = trim_cv(entry.get('linking_confidence'))
            if cluster_id not in linking_confidences:
                linking_confidences[cluster_id] = linking_confidence
            if linking_confidence != linking_confidences[cluster_id]:
                self.record_event('MULTIPLE_CLUSTER_LINKING_CONFIDENCES', linking_confidence, linking_confidences[cluster_id], cluster_id, entry.get('where'))
            clusters.append({
                'cluster_id': cluster_id,
                'linking_confidence': linking_confidence
                })
        sorted_clusters = multisort(clusters, (('linking_confidence', True),
                                               ('cluster_id', False)))
        selected_clusters = {}
        for sorted_cluster in sorted_clusters:
            if C==0: break
            cluster_id = sorted_cluster.get('cluster_id')
            if cluster_id not in selected_clusters:
                selected_clusters[cluster_id] = cluster_responses[cluster_id]
                C -= 1
        return selected_clusters

    def get_top_K_cluster_justifications(self, cluster_responses, K):
        justifications = []
        document_justifications = {}
        for entry in cluster_responses:
            document_id = entry.get('document_id')
            justification = entry.get('mention_span_text')
            confidence = trim_cv(entry.get('justification_confidence'))
            justifications.append({
                'justification': justification,
                'confidence': confidence
                })
            if document_id in document_justifications:
                self.record_event('MUTIPLE_JUSTIFICATIONS_FROM_A_DOCUMENT', justification, document_justifications[document_id], document_id, entry.get('where'))
            document_justifications[document_id] = justification
        sorted_justifications = multisort(justifications, (('confidence', True),
                                                           ('justification', False)))
        selected_justifications = {}
        for sorted_justification in sorted_justifications:
            if K == 0: break
            selected_justifications[sorted_justification.get('justification')] = 1
            K -= 1
        return selected_justifications

    def add(self, responses):
        for input_filepath in responses:
            query_id = os.path.basename(input_filepath).replace('.rq.tsv', '')
            if query_id not in self.get('pool'):
                self.get('pool')[query_id] = {}
            query_pool = self.get('pool').get(query_id)
            num_clusters = self.get('queries_to_pool').get(query_id).get('clusters')
            num_documents = self.get('queries_to_pool').get(query_id).get('documents')
            query_responses = responses.get(input_filepath)
            selected_clusters = self.get('top_C_clusters', query_responses, C=num_clusters)
            for cluster_id in selected_clusters:
                cluster_responses = selected_clusters[cluster_id]
                selected_justifications = self.get('top_K_cluster_justifications', cluster_responses, K=num_documents)
                for selected_justification in selected_justifications:
                    if self.not_in_previous_pool(query_id, selected_justification):
                        query_pool[selected_justification] = 1

    def increment_last_response_id(self, query_id):
        self.get('last_response_ids')[query_id] = self.get('last_response_id', query_id) + 1

    def load_previous_pools(self):
        logger = self.get('logger')
        previous_pool = self.get('previous_pool')
        last_response_ids = self.get('last_response_ids')
        previous_pool_dirs = self.get('previous_pool_dirs')
        if previous_pool_dirs is not None:
            for previous_pool_dir in previous_pool_dirs.split(','):
                for entry in FileHandler(logger, '{}/pool.txt'.format(previous_pool_dir)):
                    query_id = entry.get('QUERY_ID')
                    document_id = entry.get('DOCUMENT_ID')
                    mention_span = entry.get('MENTION_SPAN')
                    response_id = int(entry.get('RESPONSE_ID'))
                    if query_id not in previous_pool:
                        previous_pool[query_id] = {}
                    previous_pool[query_id]['{}:{}'.format(document_id, mention_span)] = 1
                    if query_id not in last_response_ids or last_response_ids[query_id] < response_id:
                        last_response_ids[query_id] = response_id

    def load_queries_to_pool_file(self):
        logger = self.get('logger')
        queries_to_pool = self.get('queries_to_pool')
        for entry in FileHandler(logger, self.get('queries_to_pool_file')):
            queries_to_pool[entry.get('query_id')] = {
                'query_id'  : entry.get('query_id'),
                'entrypoint': entry.get('entrypoint'),
                'clusters'  : int(entry.get('clusters')),
                'documents' : int(entry.get('documents'))
                }

    def not_in_previous_pool(self, query_id, justification):
        if query_id not in self.get('previous_pool'):
            return True
        if justification not in self.get('previous_pool').get(query_id):
            return True
        return False

    def write_output(self, output_dir):
        os.mkdir(output_dir)
        self.write_setting_files(output_dir)
        self.write_pool(output_dir)

    def write_pool(self, output_dir):
        lines = []
        for query_id in self.get('pool'):
            for mention_span in self.get('pool').get(query_id):
                mention = self.get('mention', mention_span)
                line = {
                    'CORRECTNESS'        : 'NIL',
                    'DESCRIPTOR'         : self.get('queries_to_pool').get(query_id).get('entrypoint'),
                    'DOCUMENT_ID'        : mention.get('document_id'),
                    'FQEC'               : 'NIL',
                    'MENTION_TYPE'       : 'NIL',
                    'MENTION_SOURCE'     : mention.get('modality'),
                    'QUERY_ID'           : query_id,
                    'RESPONSE_ID'        : '<ID>',
                    'MENTION_SPAN'       : '{doceid}:{span}'.format(doceid=mention.get('document_element_id'),
                                                                span=mention.get('span').__str__()),
                    'DOCUMENT_ELEMENT_ID': mention.get('document_element_id'),
                    'START_X'            : float(mention.get('span').get('start_x')),
                    'START_Y'            : float(mention.get('span').get('start_y')),
                    'END_X'              : float(mention.get('span').get('end_x')),
                    'END_Y'              : float(mention.get('span').get('end_y'))
                }
                lines.append(line)
        output = open('{dir}/pool.txt'.format(dir=output_dir), 'w')
        output.write(self.get('line'))
        query_id = None
        for line in multisort(lines, (('QUERY_ID', False),
                                      ('DOCUMENT_ID', False),
                                      ('DOCUMENT_ELEMENT_ID', False),
                                      ('START_X', False),
                                      ('START_Y', False),
                                      ('END_X', False),
                                      ('END_Y', False))):
            if query_id is None or query_id != line.get('QUERY_ID'):
                query_id = line.get('QUERY_ID')
            line['RESPONSE_ID'] = self.get('last_response_id', query_id) + 1
            output.write(self.get('line', line))
            self.increment_last_response_id(query_id)
        output.close()

    def write_setting_files(self, output_dir):
        for settings_file in ['runs_to_pool_file', 'queries_to_pool_file']:
            os.system('cp {settings_file} {output_dir}'.format(settings_file=self.get(settings_file),
                                                               output_dir=output_dir))