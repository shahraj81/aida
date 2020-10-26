"""
Class representing pool of task2 responses.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "21 October 2020"

from aida.file_handler import FileHandler
from aida.object import Object
from aida.response_set import ResponseSet
from aida.utility import multisort, trim_cv, augment_mention_object, spanstring_to_object

import datetime
import os
import subprocess

class Task2Pool(Object):
    """
    Class representing pool of task2 responses.
    """

    def __init__(self, logger, ontology_type_mappings, slot_mappings, document_mappings, document_boundaries, runs_to_pool_file, queries_to_pool_file, max_kit_size, batch_id, input_dir, previous_pools):
        super().__init__(logger)
        self.batch_id = batch_id
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
        self.input_dir = input_dir
        self.max_kit_size = max_kit_size
        self.last_response_ids = {}
        self.ontology_type_mappings = ontology_type_mappings
        self.previous_pool = {}
        self.previous_pool_dirs = previous_pools
        self.pool = {}
        self.queries_to_pool = {}
        self.queries_to_pool_file = queries_to_pool_file
        self.query_kits = {}
        self.responses = {}
        self.runs_to_pool_file = runs_to_pool_file
        self.slot_mappings = slot_mappings
        self.load_queries_to_pool_file()
        self.load_previous_pools()
        self.load_responses()

    def generate_ldc_package(self, output_dir):
        ldc_package_dir = '{output_dir}/task2_pool_{batchid}'.format(output_dir=output_dir,
                                                              batchid=self.get('batch_id').lower())
        os.system('cd {output_dir} && tar -zcf task2_pool_{batchid}.tgz.txt task2_pool_{batchid}'.format(output_dir=output_dir,
                                                                                                         batchid=self.get('batch_id').lower()))
        result = subprocess.run(['md5', '-q', '{}.tgz.txt'.format(ldc_package_dir)], stdout=subprocess.PIPE)
        md5hash = result.stdout.decode('utf-8').strip()
        ctime = os.path.getctime('{ldc_package_dir}.tgz.txt'.format(ldc_package_dir=ldc_package_dir))
        ctimestamp = datetime.datetime.fromtimestamp(ctime).__str__()
        ctimestamp = ctimestamp.replace('-', '').replace(' ', '').replace(':', '')
        ctimestamp = ctimestamp[0:12]
        os.system('mv {ldc_package_dir}.tgz.txt {ldc_package_dir}_{ctimestamp}_{md5hash}.tgz.txt'.format(ldc_package_dir=ldc_package_dir,
                                                                                                         ctimestamp=ctimestamp,
                                                                                                         md5hash=md5hash))
        print('--ldc package written to {ldc_package_dir}_{ctimestamp}_{md5hash}.tgz.txt'.format(ldc_package_dir=ldc_package_dir,
                                                                                                 ctimestamp=ctimestamp,
                                                                                                 md5hash=md5hash))

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

    def get_language(self, line):
        return self.get('document_mappings').get('language', line.get('DOCUMENT_ID'))

    def get_last_response_id(self, query_id):
        last_response_ids = self.get('last_response_ids')
        if query_id not in last_response_ids:
            return 0
        return last_response_ids.get(query_id)

    def get_query_kit(self, query_id):
        query_kits = self.get('query_kits')
        if query_id not in query_kits:
            query_kits[query_id] = {1: []}
            return query_kits.get(query_id).get(1)
        else:
            query_kit_contanier = query_kits.get(query_id)
            max_kit_id = None
            for kit_id in query_kit_contanier:
                if max_kit_id is None or max_kit_id < kit_id:
                    max_kit_id = kit_id
                query_kit = query_kit_contanier.get(kit_id)
                if len(query_kit) < self.get('max_kit_size'):
                    return query_kit
            next_kit_id = max_kit_id + 1
            query_kit = []
            query_kit_contanier[next_kit_id] = query_kit
            return query_kit

    def get_top_C_clusters(self, query_responses, C):
        cluster_responses = {}
        linking_confidences = {}
        clusters = []
        for linenum in query_responses:
            entry = query_responses.get(str(linenum))
            if not entry.get('valid'):
                self.record_event('EXPECTING_VALID_ENTRY', entry.get('where'))
            self.validate_descriptor(entry)
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
            if not entry.get('valid'):
                self.record_event('EXPECTING_VALID_ENTRY', entry.get('where'))
            self.validate_descriptor(entry)
            document_id = entry.get('document_id')
            justification = entry.get('mention_span_text')
            confidence = trim_cv(entry.get('justification_confidence'))
            justifications.append({
                'justification': justification,
                'confidence': confidence,
                'entry': entry
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
            sorted_justification.get('entry').set('pooled', 1)
            K -= 1
        return selected_justifications

    def add(self, responses):
        self.get('responses')[responses.get('runid')] = responses
        for input_filepath in responses:
            query_id = os.path.basename(input_filepath).replace('.rq.tsv', '')
            if query_id not in self.get('queries_to_pool'):
                self.record_event('DEFAULT_INFO', 'Query {} is not in queries_to_pool file (skipping {})'.format(query_id, input_filepath))
                continue
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

    def add_to_kit(self, query_id, pretty_line):
        query_kit = self.get('query_kit', query_id)
        query_kit.append(pretty_line)

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

    def load_responses(self):
        logger = self.get('logger')
        ontology_type_mappings = self.get('ontology_type_mappings')
        slot_mappings = self.get('slot_mappings')
        document_mappings = self.get('document_mappings')
        document_boundaries = self.get('document_boundaries')
        runs_to_pool_file = self.get('runs_to_pool_file')
        for entry in FileHandler(logger, runs_to_pool_file):
            run_id = entry.get('run_id')
            run_dir = '{input}/{run_id}/SPARQL-VALID-output'.format(input=self.get('input_dir'), run_id=run_id)
            responses = ResponseSet(logger, ontology_type_mappings, slot_mappings, document_mappings, document_boundaries, run_dir, run_id, 'task2')
            self.add(responses)

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

    def validate_descriptor(self, entry):
        query_id = os.path.basename(entry.get('filename')).replace('.rq.tsv', '')
        query_link_target = entry.get('query_link_target')
        link_target = entry.get('link_target')
        valid = True
        if query_link_target != link_target:
            valid = False
        if query_link_target != self.get('queries_to_pool').get(query_id).get('entrypoint'):
            valid = False
        if not valid:
            self.record_event('UNEXPECTED_ENTRYPOINT_DESCRIPTOR',
                              query_link_target,
                              link_target,
                              self.get('queries_to_pool').get(query_id).get('entrypoint'),
                              query_id,
                              self.get('queries_to_pool_file'),
                              entry.get('filename'))

    def write_output(self, output_dir):
        os.mkdir(output_dir)
        self.write_pooled_responses()
        self.write_setting_files(output_dir)
        self.write_pool(output_dir)
        self.write_kits(output_dir)
        self.generate_ldc_package(output_dir)

    def write_kits(self, output_dir):
        kit_language_map = {}
        ldc_package_dir = '{output_dir}/task2_pool_{batchid}'.format(output_dir=output_dir,
                                                              batchid=self.get('batch_id').lower())
        os.mkdir('{ldc_package_dir}'.format(ldc_package_dir=ldc_package_dir))
        os.mkdir('{ldc_package_dir}/kits'.format(ldc_package_dir=ldc_package_dir))
        query_kits = self.get('query_kits')
        for query_id in query_kits:
            query_kit_contanier = query_kits.get(query_id)
            for kit_id in query_kit_contanier:
                query_kit = query_kit_contanier.get(kit_id)
                kit_filename = '{}_{}_{}.tab'.format(self.get('batch_id'), query_id, kit_id)
                if kit_filename not in kit_language_map:
                    kit_language_map[kit_filename] = {}
                output = open('{ldc_package_dir}/kits/{kit_filename}'.format(ldc_package_dir=ldc_package_dir,
                                                                             kit_filename=kit_filename), 'w')
                for line in query_kit:
                    language = self.get('language', line)
                    kit_language_map.get(kit_filename)[language] = 1
                    output.write(self.get('line', line))
                output.close()
        kit_language_map_filepath = '{ldc_package_dir}/task2_pool_{batchid}.klm'.format(ldc_package_dir=ldc_package_dir,
                                                                                        batchid=self.get('batch_id').lower()) 
        with open(kit_language_map_filepath, 'w') as output:
            for kit_filename in kit_language_map:
                languages = ','.join(sorted(kit_language_map.get(kit_filename)))
                output.write('{kit_filename}\t{languages}\n'.format(kit_filename=kit_filename,
                                                                  languages=languages))

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
                    'MENTION_SOURCE'     : mention.get('modality').upper(),
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
            self.add_to_kit(query_id, line)
            pretty_line = self.get('line', line)
            output.write(pretty_line)
            self.increment_last_response_id(query_id)
        output.close()

    def write_pooled_responses(self):
        for run_id in self.get('responses'):
            run_responses = self.get('responses').get(run_id)
            pooled_output_dir = run_responses.get('path').replace('VALID', 'POOLED')
            if os.path.exists(pooled_output_dir):
                self.record_event('DEFAULT_CRITICAL_ERROR', 'Path {} exists.'.format(pooled_output_dir))
            print('--writing pooled output from run \'{}\' to {}'.format(run_id, pooled_output_dir))
            run_responses.write_pooled_responses(pooled_output_dir)

    def write_setting_files(self, output_dir):
        for settings_file in ['runs_to_pool_file', 'queries_to_pool_file']:
            os.system('cp {settings_file} {output_dir}'.format(settings_file=self.get(settings_file),
                                                               output_dir=output_dir))