"""
Class representing pool of task2 responses.
"""
from aida import document

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 October 2020"

from aida.object import Object
from aida.utility import multisort, trim_cv, augment_mention_object, spanstring_to_object

import os

class Task2Pool(Object):
    """
    Class representing pool of task2 responses.
    """

    def __init__(self, logger, queries, document_mappings, document_boundaries):
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
        self.pool = {}
        self.queries = queries

    def get_line(self, columns=None):
        if columns is None:
            return '{}\n'.format('\t'.join(self.get('header')))
        else:
            return '{}\n'.format('\t'.join([columns[column_name] for column_name in self.get('header')]))

    def get_mention(self, span_string):
        logger = self.get('logger')
        return augment_mention_object(spanstring_to_object(logger, span_string, self.get('code_location')),
                                      self.get('document_mappings'),
                                      self.get('document_boundaries'))

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
            num_clusters = self.get('queries').get(query_id).get('clusters')
            num_documents = self.get('queries').get(query_id).get('documents')
            query_responses = responses.get(input_filepath)
            selected_clusters = self.get('top_C_clusters', query_responses, C=num_clusters)
            for cluster_id in selected_clusters:
                cluster_responses = selected_clusters[cluster_id]
                selected_justifications = self.get('top_K_cluster_justifications', cluster_responses, K=num_documents)
                for selected_justification in selected_justifications:
                    query_pool[selected_justification] = 1

    def write_output(self, output_dir):
        os.mkdir(output_dir)
        output = open('{dir}/pool.txt'.format(dir=output_dir), 'w')
        output.write(self.get('line'))
        for query_id in self.get('pool'):
            for mention_span in self.get('pool').get(query_id):
                mention = self.get('mention', mention_span)
                columns = {
                    'CORRECTNESS'    : 'NIL',
                    'DESCRIPTOR'     : self.get('queries').get(query_id).get('entrypoint'),
                    'DOCUMENT_ID'    : mention.get('document_id'),
                    'FQEC'           : 'NIL',
                    'MENTION_TYPE'   : 'NIL',
                    'MENTION_SOURCE' : mention.get('modality'),
                    'QUERY_ID'       : query_id,
                    'RESPONSE_ID'    : '<ID>',
                    'MENTION_SPAN'   : '{doceid}:{span}'.format(doceid=mention.get('document_element_id'),
                                                                span=mention.get('span').__str__())
                }
                line = self.get('line', columns)
                output.write(line)
        output.close()