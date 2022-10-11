"""
AIDA main script for filtering responses.

This scripts runs on validated output and produces only responses that
contained mentions in the fully annotated regions.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "16 August 2020"

from aida.logger import Logger
from aida.object import Object
from aida.response_set import ResponseSet
from aida.encodings import Encodings
from aida.core_documents import CoreDocuments
from aida.document_mappings import DocumentMappings
from aida.excel_workbook import ExcelWorkbook
from aida.file_handler import FileHandler
from aida.text_boundaries import TextBoundaries
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.utility import get_cost_matrix, get_intersection_over_union, trim_cv
from aida.video_boundaries import VideoBoundaries
from generate_aif import LDCTypeToDWDNodeMapping

import argparse
import json
import os
import pandas as pd
import requests
import statistics
import sys
import time

from munkres import Munkres
from tqdm import tqdm

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

class AlignClusters(Object):
    def __init__(self, logger, document_mappings, similarity, responses, IOU_THRESHOLDS):
        super().__init__(logger)
        self.document_mappings = document_mappings
        self.IOU_THRESHOLDS = {}
        for key_and_value in IOU_THRESHOLDS.split(','):
            language, modality, threshold = key_and_value.split(':')
            self.IOU_THRESHOLDS[self.get('iou_threshold_key', language, modality)] = float(threshold)
        self.responses = responses
        self.similarity = similarity
        self.weighted = 'no'
        self.alignments = {}
        if self.get('similarity').get('KGTK_SIMILARITY_SERVICE_API'):
            self.get('similarity').build_cache(document_mappings, responses)
        self.align_clusters()
        if self.get('similarity').get('KGTK_SIMILARITY_SERVICE_API') and self.get('similarity').get('CACHE'):
            self.get('similarity').flush_cache()

    def get_cluster(self, gold_or_system, document_id, cluster_id):
        return self.get('responses').get(gold_or_system).get('document_clusters').get(document_id).get(cluster_id)

    def get_cluster_types(self, gold_or_system, document_id, cluster_id):
        cluster_types = set()
        for entry in self.get('responses').get(gold_or_system).get('document_clusters').get(document_id).get(cluster_id).get('entries').values():
            cluster_types.add((trim_cv(entry.get('cluster_membership_confidence')) * trim_cv(entry.get('type_statement_confidence')), entry.get('cluster_type')))
        return cluster_types

    def get_document_cluster_similarities(self, document_id):
        similarities = {}
        for gold_cluster_id in sorted(self.get('responses').get('gold').get('document_clusters').get(document_id) or []):
            for system_cluster_id in sorted(self.get('responses').get('system').get('document_clusters').get(document_id) or []):
                similarity = self.get('metatype_similarity', document_id, 'gold', gold_cluster_id, 'system', system_cluster_id)
                if similarity > 0:
                    similarity *= self.get('type_similarity', document_id, 'gold', gold_cluster_id, 'system', system_cluster_id)
                    similarity *= self.get('mention_similarity', document_id, 'gold', gold_cluster_id, 'system', system_cluster_id)
                similarities.setdefault(gold_cluster_id, {})[system_cluster_id] = similarity
        return similarities

    def get_mention_similarity(self, document_id, system_or_gold1, cluster_id1, system_or_gold2, cluster_id2):
        cluster1 = self.get('cluster', system_or_gold1, document_id, cluster_id1)
        cluster2 = self.get('cluster', system_or_gold2, document_id, cluster_id2)

        # align mentions
        mentions = {
            'cluster1': list(cluster1.get('mentions').values()),
            'cluster2': list(cluster2.get('mentions').values())
            }

        # build the mapping table
        mappings = {}
        for clusternum in mentions:
            mappings[clusternum] = {'id_to_index': {}, 'index_to_id': {}}
            index = 0;
            for mention in mentions[clusternum]:
                mappings[clusternum]['id_to_index'][mention.get('ID')] = index
                mappings[clusternum]['index_to_id'][index] = mention.get('ID')
                index += 1

        # build the similarities table
        similarities = {}
        for mention1 in mentions['cluster1']:
            document_element_id = mention1.get('document_element_id')
            modality = self.get('document_mappings').get('modality', document_element_id)
            language = self.get('document_mappings').get('language', document_element_id)
            for mention2 in mentions['cluster2']:
                if mention1.get('ID') not in similarities:
                    similarities[mention1.get('ID')] = {}
                iou = get_intersection_over_union(mention1, mention2)
                iou = 0 if iou < self.get('iou_threshold', language, modality) else iou
                similarities[mention1.get('ID')][mention2.get('ID')] = iou

        # record alignment
        cluster1_and_cluster2_ids = '::'.join([cluster_id1, cluster_id2])
        alignment_type = '{}_to_{}'.format(system_or_gold1, system_or_gold2)
        self.record_alignment(document_id, 'mention', alignment_type, cluster1_and_cluster2_ids, similarities, mappings)
        alignment = self.get('alignments').get(document_id).get('mention').get(cluster1_and_cluster2_ids)

        similarity = 0
        for mention_id1 in alignment.get(alignment_type):
            mention_id2 = alignment.get(alignment_type).get(mention_id1).get('aligned_to')
            if similarities[mention_id1][mention_id2] > 0:
                # lenient similarity computation
                if self.get('weighted') == 'no':
                    # total mentions
                    similarity += 1
                elif self.get('weighted') == 'yes':
                    # total iou
                    similarity += similarities[mention_id1][mention_id2]
        return similarity

    def get_metatype_similarity(self, document_id, system_or_gold1, cluster1, system_or_gold2, cluster2):
        metatype1 = self.get('cluster', system_or_gold1, document_id, cluster1).get('metatype')
        metatype2 = self.get('cluster', system_or_gold2, document_id, cluster2).get('metatype')
        if metatype1 == metatype2:
            return 1.0
        return 0.0

    def get_iou_threshold(self, language, modality):
        key = self.get('iou_threshold_key', language, modality)
        if key not in self.get('IOU_THRESHOLDS'):
            self.record_event('DEFAULT_CRITICAL_ERROR', 'missing IOU threshold for language={} modality={}'.format(language, modality))
        return self.get('IOU_THRESHOLDS').get(key)

    def get_iou_threshold_key(self, language, modality):
        if modality and language:
            return '{}:{}'.format(language, modality).lower()
        self.record_event('DEFAULT_CRITICAL_ERROR', 'modality and language both need to be specified')

    def get_type_similarity(self, document_id, system_or_gold1, cluster_id1, system_or_gold2, cluster_id2, combine=statistics.mean):
        cluster1_types = self.get('cluster_types', system_or_gold1, document_id, cluster_id1)
        cluster2_types = self.get('cluster_types', system_or_gold2, document_id, cluster_id2)
        similarities = []
        for (conf1, q1) in cluster1_types:
            for (conf2, q2) in cluster2_types:
                similarities.append(conf1 * conf2 * self.get('similarity').similarity(q1, q2))
        similarity = combine(similarities)
        return similarity

    def align_clusters(self):
        mappings = {}
        filetype_to_clusternum_mapping = {
            'gold': 'cluster1',
            'system': 'cluster2'
            }
        for document_id in tqdm(self.get('document_mappings').get('core_documents'), desc='Aligning clusters'):
            self.record_event('DEFAULT_INFO', 'aligning clusters from document {}'.format(document_id))
            for filetype in ['gold', 'system']:
                clusternum = filetype_to_clusternum_mapping[filetype]
                mappings[clusternum] = {'id_to_index': {}, 'index_to_id': {}}
                index = 0
                for cluster_id in sorted(self.get('responses').get(filetype).get('document_clusters').get(document_id) or []):
                    mappings[clusternum]['id_to_index'][cluster_id] = index
                    mappings[clusternum]['index_to_id'][index] = cluster_id
                    index += 1
            self.record_alignment(document_id, 'cluster', 'gold_to_system', None, self.get('document_cluster_similarities', document_id), mappings)

    def init_alignment(self, document_id, cluster_or_mention, alignment_type, cluster1_and_cluster2_ids):
        if cluster1_and_cluster2_ids is None:
            if cluster_or_mention == 'cluster':
                self.get('alignments').setdefault(document_id, {}).setdefault(cluster_or_mention, {})[alignment_type] = {}
                return self.get('alignments').get(document_id).get(cluster_or_mention)
            else:
                self.record_event('DEFAULT_CRITICAL_ERROR', 'cluster_id should be provided when aligning mentions')
        else:
            if cluster_or_mention == 'mention':
                self.get('alignments').setdefault(document_id, {}).setdefault(cluster_or_mention, {}).setdefault(cluster1_and_cluster2_ids, {})[alignment_type] = {}
                return self.get('alignments').get(document_id).get(cluster_or_mention).get(cluster1_and_cluster2_ids)
            else:
                self.record_event('DEFAULT_CRITICAL_ERROR', 'cluster_id should be None when aligning clusters')

    def is_aligned_to_a_gold_cluster(self, document_id, cluster_id):
        document_alignments = self.get('alignments').get(document_id)
        if document_alignments and cluster_id in document_alignments.get('cluster').get('system_to_gold'):
            return True
        return False

    def lookup_similarity(self, similarities, item_id1, item_id2):
        if item_id1 in similarities:
            if item_id2 in similarities.get(item_id1):
                return similarities.get(item_id1).get(item_id2)
        return 0

    def record_alignment(self, document_id, cluster_or_mention, alignment_type, cluster1_and_cluster2_ids, similarities, mappings):
        i1, i2 = alignment_type.split('_to_')
        inverted_alignment_type = '{}_to_{}'.format(i2, i1)
        if len(similarities):
            alignment = self.init_alignment(document_id, cluster_or_mention, alignment_type, cluster1_and_cluster2_ids)
            if inverted_alignment_type != alignment_type:
                alignment.setdefault(inverted_alignment_type, {})
            cost_matrix = get_cost_matrix(similarities, mappings, type_a='cluster1', type_b='cluster2')
            for item1_index, item2_index in Munkres().compute(cost_matrix):
                item1_id = mappings['cluster1']['index_to_id'][item1_index]
                item2_id = mappings['cluster2']['index_to_id'][item2_index]
                similarity = self.lookup_similarity(similarities, item1_id, item2_id)
                if similarity > 0:
                    alignment.get(alignment_type)[item1_id] = {
                            'aligned_to': item2_id,
                            'aligned_similarity': similarity
                        }
                    if inverted_alignment_type != alignment_type:
                        alignment.get(inverted_alignment_type)[item2_id] = {
                                'aligned_to': item1_id,
                                'aligned_similarity': similarity
                            }
                self.record_event('ALIGNMENT_INFO', document_id, cluster_or_mention, cluster1_and_cluster2_ids, item1_id, item2_id, similarity)

    def print_similarities(self, output_dir):
        def tostring(entry=None):
            columns = ['metatype', 'system_or_gold1', 'cluster1', 'system_or_gold2', 'cluster2', 'type_similarity', 'similarity']
            values = []
            for column in columns:
                value = column if entry is None else str(entry.get(column))
                values.append(value)
            return '{}\n'.format('\t'.join(values))
        os.mkdir(output_dir)
        for document_id in tqdm(self.get('alignments'), desc='Printing similarities'):
            cluster_ids = {
                'system': list(sorted(self.get('alignments').get(document_id).get('cluster').get('system_to_gold').keys())),
                'gold': list(sorted(self.get('alignments').get(document_id).get('cluster').get('gold_to_system').keys()))
                }
            with open(os.path.join(output_dir, '{}.tab'.format(document_id)), 'w') as program_output:
                program_output.write(tostring())
                for system_or_gold1, system_or_gold2 in [('system', 'system'), ('system', 'gold'), ('gold', 'gold')]:
                    for cluster1 in cluster_ids.get(system_or_gold1):
                        metatype = self.get('cluster', system_or_gold1, document_id, cluster1).get('metatype')
                        for cluster2 in cluster_ids.get(system_or_gold2):
                            similarity = self.get('metatype_similarity', document_id, system_or_gold1, cluster1, system_or_gold2, cluster2)
                            if similarity > 0:
                                type_similarity = self.get('type_similarity', document_id, system_or_gold1, cluster1, system_or_gold2, cluster2)
                                similarity *= self.get('mention_similarity', document_id, system_or_gold1, cluster1, system_or_gold2, cluster2)
                                similarity *= type_similarity
                                entry = {
                                    'metatype': metatype,
                                    'system_or_gold1': system_or_gold1,
                                    'cluster1': cluster1,
                                    'system_or_gold2': system_or_gold2,
                                    'cluster2': cluster2,
                                    'type_similarity': type_similarity,
                                    'similarity': similarity,
                                    }
                                program_output.write(tostring(entry))

    def print_alignment(self, output_dir):
        def tostring(columns, entry=None):
            values = []
            for column in columns:
                value = column if entry is None else str(entry.get(column))
                values.append(value)
            return '{}\n'.format('\t'.join(values))
        os.mkdir(output_dir)
        cluster_alignment_columns = ['metatype', 'system_cluster', 'gold_cluster', 'similarity']
        mention_alignment_columns = ['metatype', 'system_cluster', 'gold_cluster', 'system_mention', 'gold_mention', 'similarity']
        # print cluster alignment
        cluster_alignment_output_dir = os.path.join(output_dir, 'cluster')
        os.mkdir(cluster_alignment_output_dir)
        mention_alignment_output_dir = os.path.join(output_dir, 'mention')
        os.mkdir(mention_alignment_output_dir)
        for document_id in tqdm(self.get('alignments'), desc='Printing alignment'):
            document_cluster_alignment = self.get('alignments').get(document_id).get('cluster').get('gold_to_system')
            with open(os.path.join(cluster_alignment_output_dir, '{}.tab'.format(document_id)), 'w') as cluster_alignment_program_output:
                with open(os.path.join(mention_alignment_output_dir, '{}.tab'.format(document_id)), 'w') as mention_alignment_program_output:
                    cluster_alignment_program_output.write(tostring(cluster_alignment_columns))
                    mention_alignment_program_output.write(tostring(mention_alignment_columns))
                    document_cluster_mention_alignment = self.get('alignments').get(document_id).get('mention')
                    # print aligned clusters
                    aligned_clusters = {
                        'gold': set(),
                        'system': set()
                        }
                    for gold_cluster_id in sorted(document_cluster_alignment):
                        system_cluster_id = document_cluster_alignment.get(gold_cluster_id).get('aligned_to')
                        aligned_clusters.get('gold').add(gold_cluster_id)
                        aligned_clusters.get('system').add(system_cluster_id)
                        similarity = document_cluster_alignment.get(gold_cluster_id).get('aligned_similarity')
                        metatype = self.get('cluster', 'gold', document_id, gold_cluster_id).get('metatype')
                        entry = {
                            'metatype': metatype,
                            'system_cluster': system_cluster_id,
                            'gold_cluster': gold_cluster_id,
                            'similarity': similarity
                            }
                        cluster_alignment_program_output.write(tostring(cluster_alignment_columns, entry))
                        # print mention alignment for the pair of aligned gold and system clusters
                        cluster1_and_cluster2_ids = '::'.join([gold_cluster_id, system_cluster_id])
                        alignment_type = 'gold_to_system'
                        for gold_mention_id in document_cluster_mention_alignment.get(cluster1_and_cluster2_ids).get(alignment_type):
                            system_mention_id = document_cluster_mention_alignment.get(cluster1_and_cluster2_ids).get(alignment_type).get(gold_mention_id).get('aligned_to')
                            similarity = document_cluster_mention_alignment.get(cluster1_and_cluster2_ids).get(alignment_type).get(gold_mention_id).get('aligned_similarity')
                            entry = {
                                'metatype': metatype,
                                'system_cluster': system_cluster_id,
                                'gold_cluster': gold_cluster_id,
                                'system_mention': system_mention_id,
                                'gold_mention': gold_mention_id,
                                'similarity': similarity
                                }
                            mention_alignment_program_output.write(tostring(mention_alignment_columns, entry))
                    # print unaligned gold and system clusters information
                    for system_or_gold in ['gold', 'system']:
                        for cluster_id in self.get('responses').get(system_or_gold).get('document_clusters').get(document_id):
                            if cluster_id in aligned_clusters.get(system_or_gold): continue
                            entry = {
                                'metatype': self.get('cluster', system_or_gold, document_id, cluster_id).get('metatype'),
                                'system_cluster': cluster_id if system_or_gold == 'system' else 'None',
                                'gold_cluster': cluster_id if system_or_gold == 'gold' else 'None',
                                'similarity': 0
                                }
                            cluster_alignment_program_output.write(tostring(cluster_alignment_columns, entry))

class ResponseFilter(Object):
    def __init__(self, logger, alignment, similarity):
        super().__init__(logger)
        self.alignment = alignment
        self.similarity = similarity
        self.alignments = {}
        self.filtered_clusters = {}

    def apply(self, responses):
        for schema_name in ['AIDA_PHASE3_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_TM_RESPONSE']:
            for input_filename in tqdm(responses, desc='Applying filter ({})'.format(schema_name)):
                for linenum in responses.get(input_filename):
                    entry = responses.get(input_filename).get(str(linenum))
                    if entry.get('schema').get('name') == schema_name:
                        self.apply_filter_to_entry(entry, schema_name)

    def apply_filter_to_entry(self, entry, schema_name):
        logger = self.get('logger')
        filtered_clusters = self.get('filtered_clusters')

        if schema_name not in ['AIDA_PHASE3_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_TM_RESPONSE']:
            logger.record_event('DEFAULT_CRITICAL_ERROR', 'Unexpected schema name: {}'.format(schema_name), entry.get('code_location'))

        passes_filter = False

        if schema_name == 'AIDA_PHASE3_TASK1_AM_RESPONSE':
            cluster_type_to_keys = {
                        'subject': '{}:{}'.format(entry.get('kb_document_id'), entry.get('subject_cluster').get('ID')),
                        'object': '{}:{}'.format(entry.get('kb_document_id'), entry.get('object_cluster').get('ID'))
                        }
            passes_filter = True
            for cluster_type in cluster_type_to_keys:
                key = cluster_type_to_keys[cluster_type]
                if key in filtered_clusters:
                    if not filtered_clusters[key]:
                        passes_filter = False
                        cluster_id = entry.get('{}_cluster'.format(cluster_type)).get('ID')
                        logger.record_event('CLUSTER_NOT_ANNOTATED', cluster_id, entry.get('where'))
                        break
                else:
                    logger.record_event('MISSING_ENTRY_IN_LOOKUP_ERROR', key, 'filtered_clusters', entry.get('code_location'))

        elif schema_name == 'AIDA_PHASE3_TASK1_CM_RESPONSE':
            key = '{}:{}'.format(entry.get('kb_document_id'), entry.get('cluster').get('ID'))
            cluster_type = entry.get('cluster_type')
            if key not in filtered_clusters:
                filtered_clusters[key] = False
            if self.passes_filter(entry):
                passes_filter = True
                filtered_clusters[key] = True
            else:
                logger.record_event('MENTION_NOT_ANNOTATED', entry.get('mention_span_text'), entry.get('where'))

        elif schema_name == 'AIDA_PHASE3_TASK1_TM_RESPONSE':
            cluster_id = entry.get('subject_cluster').get('ID')
            key = '{}:{}'.format(entry.get('kb_document_id'), cluster_id)
            if key in filtered_clusters:
                passes_filter = filtered_clusters[key]
                if not passes_filter:
                    logger.record_event('CLUSTER_NOT_ANNOTATED', cluster_id, entry.get('where'))
            else:
                logger.record_event('MISSING_ENTRY_IN_LOOKUP_ERROR', key, 'filtered_clusters', entry.get('code_location'))

        entry.set('passes_filter', passes_filter)

    def passes_filter(self, entry):
        # the entry passes filter if
        ## - the corresponding system cluster is aligned to a gold cluster, or 
        if self.get('alignment').is_aligned_to_a_gold_cluster(entry.get('document_id'), entry.get('cluster').get('ID')):
            return True
        ## - if the cluster type:
            # - matches one of the taggable DWD types, or
            # - is a synonym of a taggable DWD type, or
            # - is similar enough to a taggable DWD type
        if self.get('similarity').passes_filter(entry.get('cluster_type')):
            return True
        return False

class Similarity(Object):
    def __init__(self, logger, taggable_dwd_ontology, alpha, combine=statistics.mean, LOCK=None, ACQUIRE_LOCK_WAIT=10, NN_SIMILARITY_SCORE=0.9, SIMILARITY_TYPES=None, KGTK_SIMILARITY_SERVICE_API=None, CACHE=None):
        super().__init__(logger)
        self.alpha = alpha
        self.combine = combine
        self.taggable_dwd_ontology = taggable_dwd_ontology
        self.ACQUIRE_LOCK_WAIT = ACQUIRE_LOCK_WAIT
        self.CACHE = CACHE
        self.LOCK = LOCK
        self.NN_SIMILARITY_SCORE = NN_SIMILARITY_SCORE
        self.SIMILARITY_TYPES = [t.strip() for t in SIMILARITY_TYPES.split(',')]
        self.KGTK_SIMILARITY_SERVICE_API = None if KGTK_SIMILARITY_SERVICE_API=='None' else KGTK_SIMILARITY_SERVICE_API
        self.cached_similarity_scores = {}

    def acquire_lock(self):
        lock = self.get('LOCK')
        if lock is None:
            self.record_event('DEFAULT_CRITICAL_ERROR', 'lock file needs to be specified')
        waiting_on_lock = True
        self.record_event('DEFAULT_INFO', 'waiting on lock in order to flush the cache to file')
        print('--waiting on lock ({}) in order to flush the cache to file '.format(lock), end='', flush=True)
        while(waiting_on_lock):
            if not os.path.exists(lock):
                with open(lock, 'w'):
                    pass
                if os.path.exists(lock):
                    waiting_on_lock = False
            else:
                print('.', end='', flush=True)
                time.sleep(self.get('ACQUIRE_LOCK_WAIT'))
        print(' acquired')

    def build_cache(self, document_mappings, responses):
        def call_kgtk_api(input_files, url):
            for input_file in tqdm(sorted(input_files, key=lambda f: int(f.split('.')[0].split('_')[2])), desc='calling tqdm-similarity api'):
                file_name = os.path.basename(input_file)
                files = {
                    'file': (file_name, open(input_file, mode='rb'), 'application/octet-stream')
                }
                resp = requests.post(url, files=files, params={'similarity_types': ','.join(sorted(self.get('SIMILARITY_TYPES')))})
                s = json.loads(resp.json())
                output_file = '{}_output.txt'.format(input_file.split('.txt')[0])
                pd.DataFrame(s).to_csv(output_file, index=False, sep='\t')

        # read cached similarities passed as input
        if self.get('CACHE') is not None and os.path.exists(self.get('CACHE')):
            for entry in FileHandler(self.get('logger'), self.get('CACHE')):
                self.cache(entry.get('q1'), entry.get('q2'), entry.get('similarity'))

        qnode_pairs = set()
        for document_id in document_mappings.get('core_documents'):
            for system_or_gold1, system_or_gold2 in [('system', 'system'), ('system', 'gold'), ('gold', 'gold')]:
                for cluster_id1 in responses.get(system_or_gold1).get('document_clusters').get(document_id) or []:
                    cluster1_types = self.get('cluster_types', responses, system_or_gold1, document_id, cluster_id1)
                    for cluster_id2 in responses.get(system_or_gold2).get('document_clusters').get(document_id) or []:
                        cluster2_types = self.get('cluster_types', responses, system_or_gold2, document_id, cluster_id2)
                        for cluster1_type in cluster1_types:
                            for cluster2_type in cluster2_types:
                                qnode_pairs.add((cluster1_type[1], cluster2_type[1]))

            for cluster_id in responses.get('system').get('document_clusters').get(document_id) or []:
                cluster_types = self.get('cluster_types', responses, 'system', document_id, cluster_id)
                for cluster_type in cluster_types:
                    taggable_dwd_ontology = self.get('taggable_dwd_ontology')
                    if not taggable_dwd_ontology.passes_filter(cluster_type):
                        for taggable_dwd_type in taggable_dwd_ontology.get('taggable_dwd_types'):
                            qnode_pairs.add((cluster_type[1], taggable_dwd_type))

        # generate input files to be used by kgtk similarity service batch api calls
        max_entries = 25
        count = 0
        filenum = 0
        input_files = set()
        cached_output = None
        for (q1, q2) in sorted(qnode_pairs):
            if q1 == q2: continue
            if self.get('cached_similarity_score', q1, q2) is not None: continue
            if self.get('taggable_dwd_ontology').is_synonym(q1, q2): continue
            if count == 0:
                if cached_output is not None:
                    cached_output.close()
                    cached_output = None
                filename = '/tmp/kgtk_cache_{}.txt'.format(filenum)
                cached_output = open(filename, 'w')
                cached_output.write('q1\tq2\n')
                input_files.add(filename)
                filenum += 1
                count = max_entries
            count -= 1
            cached_output.write('{}\t{}\n'.format(q1, q2))

        if cached_output is not None: cached_output.close()

        call_kgtk_api(input_files, self.get('KGTK_SIMILARITY_SERVICE_API'))

        # load the similarity output files
        for input_file in input_files:
            output_file = '{}_output.txt'.format(input_file.split('.txt')[0])
            for entry in FileHandler(self.get('logger'), output_file):
                q1 = entry.get('q1')
                q2 = entry.get('q2')
                similarity = []
                for similarity_type in self.get('SIMILARITY_TYPES'):
                    similarity_value = entry.get(similarity_type)
                    similarity_value = 0.0 if similarity_value == '' else similarity_value
                    similarity.append(float(similarity_value))
                score = self.get('combine')(similarity) if len(similarity) else 0
                self.cache(q1, q2, score)

    def cache(self, q1, q2, similarity):
        self.get('cached_similarity_scores').setdefault(q1, {})[q2] = float(similarity)

    def flush_cache(self):
        if self.get('CACHE'):
            self.acquire_lock()
            # reload cache
            for entry in FileHandler(self.get('logger'), self.get('CACHE')):
                self.cache(entry.get('q1'), entry.get('q2'), entry.get('similarity'))
            # write the updated cache to file
            with open(self.get('CACHE'), 'w') as program_output:
                program_output.write('q1\tq2\tsimilarity\n')
                for q1 in tqdm(sorted(self.get('cached_similarity_scores').keys()), desc='writing cache to file'):
                    for q2 in sorted(self.get('cached_similarity_scores').get(q1).keys()):
                        similarity = self.get('cached_similarity_scores').get(q1).get(q2)
                        program_output.write('{}\t{}\t{}\n'.format(q1, q2, similarity))
            self.release_lock()

    def get_cached_similarity_score(self, q1, q2):
        if q1 in self.get('cached_similarity_scores'):
            if q2 in self.get('cached_similarity_scores').get(q1):
                return self.get('cached_similarity_scores').get(q1).get(q2)
        return None

    def get_cluster_types(self, responses, gold_or_system, document_id, cluster_id):
        cluster_types = set()
        for entry in responses.get(gold_or_system).get('document_clusters').get(document_id).get(cluster_id).get('entries').values():
            cluster_types.add((trim_cv(entry.get('cluster_membership_confidence')) * trim_cv(entry.get('type_statement_confidence')), entry.get('cluster_type')))
        return cluster_types

    def release_lock(self):
        os.remove(self.get('LOCK'))

    def similarity(self, q1, q2):
        if q1 == q2:
            return 1.0
        if self.get('taggable_dwd_ontology').is_synonym(q1, q2):
            return 1.0
        similarity = 0.0
        if self.get('taggable_dwd_ontology').is_near_neighbor(q1, q2):
            similarity = self.get('NN_SIMILARITY_SCORE')
        if self.get('KGTK_SIMILARITY_SERVICE_API') is not None:
            cached_similarity_score = self.get('cached_similarity_score', q1, q2)
            if cached_similarity_score is not None:
                if similarity > cached_similarity_score:
                    cached_similarity_score = similarity
                    self.cache(q1, q2, cached_similarity_score)
                return cached_similarity_score
            kgtk_similarity_value = self.get('kgtk_similarity_value', q1, q2)
            if kgtk_similarity_value > similarity:
                similarity = kgtk_similarity_value
            self.cache(q1, q2, similarity)
        return similarity

    def get_kgtk_similarity_value(self, q1, q2):
        url = self.get('KGTK_SIMILARITY_SERVICE_API')
        similarity = []
        for similarity_type in self.get('SIMILARITY_TYPES'):
            while True:
                try:
                    resp = requests.get(url,
                                        params={
                                            'q1': q1,
                                            'q2': q2,
                                            'similarity_type': similarity_type})
                    break
                except ConnectionError as exception:
                    print('Exception: {}'.format(exception))
                    print('retrying ...')
                    time.sleep(5)
            json_struct = json.loads(resp.text)
            if 'error' not in json_struct:
                similarity.append(1.0 if json_struct.get('similarity') > 1.0 else json_struct.get('similarity'))
        return self.get('combine')(similarity) if len(similarity) else 0.0

    def passes_filter(self, cluster_type):
        taggable_dwd_ontology = self.get('taggable_dwd_ontology')
        if taggable_dwd_ontology.passes_filter(cluster_type):
            return True
        for taggable_dwd_type in taggable_dwd_ontology.get('taggable_dwd_types'):
            if self.similarity(cluster_type, taggable_dwd_type) > self.get('alpha'):
                return True
        return False

class TaggableDWDOntology(Object):
    def __init__(self, logger, taggable_ldc_ontology_filename, overlay_filename):
        self.logger = logger
        self.type_mappings = LDCTypeToDWDNodeMapping(logger, overlay_filename)
        self.taggable_ldc_ontology = ExcelWorkbook(logger, taggable_ldc_ontology_filename)
        self.taggable_dwd_types = {}
        for ere_type in ['events', 'entities', 'relations']:
            ere_type_data = self.taggable_ldc_ontology.get('worksheets').get(ere_type).get('entries')
            for entry in ere_type_data:
                ldc_type = '{}.{}.{}'.format(entry.get('Type'), entry.get('Subtype'), entry.get('Sub-subtype')).lower()
                ldc_type = ldc_type.replace('.unspecified.unspecified', '')
                ldc_type = ldc_type.replace('.unspecified', '')
                if ldc_type in self.type_mappings.get('mapping'):
                    for mapped_dwd_type in self.type_mappings.get('mapping').get(ldc_type):
                        self.taggable_dwd_types.setdefault(mapped_dwd_type, set()).add(ldc_type)

    def passes_filter(self, cluster_type):
        # a cluster passes filter if the cluster_type is a taggable dwd type
        # or it is a synonym of a taggable dwd type
        if cluster_type in self.get('taggable_dwd_types'):
            return True
        for taggable_dwd_type in self.get('taggable_dwd_types'):
            if self.is_synonym(cluster_type, taggable_dwd_type):
                return True
        return False

    def is_near_neighbor(self, q1, q2):
        near_neighbors = self.get('type_mappings').get('near_neighbors')
        for (t1, t2) in ((q1, q2), (q2, q1)):
            if t1 in near_neighbors:
                if t2 in near_neighbors.get(t1):
                    return True
        return False

    def is_synonym(self, q1, q2):
        synonyms = self.get('type_mappings').get('synonyms')
        for (t1, t2) in ((q1, q2), (q2, q1)):
            if t1 in synonyms:
                if t2 in synonyms.get(t1):
                    return True
        return False

def check_path(args):
    check_for_paths_existance([args.log_specifications,
                               args.encodings,
                               args.core_documents,
                               args.parent_children,
                               args.sentence_boundaries,
                               args.image_boundaries,
                               args.keyframe_boundaries,
                               args.video_boundaries,
                               args.taggable_ldc_ontology,
                               args.overlay,
                               args.input])
    check_for_paths_non_existance([args.similarities, args.alignment, args.output])

def check_for_paths_existance(paths):
    for path in paths:
        if not os.path.exists(path):
            print('Error: Path {} does not exist'.format(path))
            exit(ERROR_EXIT_CODE)

def check_for_paths_non_existance(paths):
    for path in paths:
        if os.path.exists(path):
            print('Error: Path {} exists'.format(path))
            exit(ERROR_EXIT_CODE)

def filter_responses(args):
    logger = Logger(args.log, args.log_specifications, sys.argv)
    logger.record_event('DEFAULT_INFO', 'filtering started')
    document_mappings = DocumentMappings(logger,
                                         args.parent_children,
                                         Encodings(logger, args.encodings),
                                         CoreDocuments(logger, args.core_documents))
    text_boundaries = TextBoundaries(logger, args.sentence_boundaries)
    image_boundaries = ImageBoundaries(logger, args.image_boundaries)
    video_boundaries = VideoBoundaries(logger, args.video_boundaries)
    keyframe_boundaries = KeyFrameBoundaries(logger, args.keyframe_boundaries)
    document_boundaries = {
        'text': text_boundaries,
        'image': image_boundaries,
        'keyframe': keyframe_boundaries,
        'video': video_boundaries
        }
    taggable_dwd_ontology = TaggableDWDOntology(logger, args.taggable_ldc_ontology, args.overlay)
    system_responses = ResponseSet(logger, document_mappings, document_boundaries, args.input, args.runid, 'task1')
    gold_responses = ResponseSet(logger, document_mappings, document_boundaries, args.gold, 'gold', 'task1')
    similarity = Similarity(logger, taggable_dwd_ontology, args.alpha, LOCK=args.lock, ACQUIRE_LOCK_WAIT=args.wait, NN_SIMILARITY_SCORE=args.near_neighbor_similarity_value, SIMILARITY_TYPES=args.similarity_types, KGTK_SIMILARITY_SERVICE_API=args.kgtk_api, CACHE=args.cache)
    alignment = AlignClusters(logger, document_mappings, similarity, {'gold': gold_responses, 'system': system_responses}, IOU_THRESHOLDS=args.iou_thresholds)
    response_filter = ResponseFilter(logger, alignment, similarity)
    response_filter.apply(system_responses)
    # write alignment and similarities
    alignment.print_similarities(args.similarities)
    alignment.print_alignment(args.alignment)
    # write filtered output
    os.mkdir(args.output)
    for input_filename in system_responses:
        output_filename = input_filename.replace(system_responses.get('path'), args.output)
        dirname = os.path.dirname(output_filename)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        file_container = system_responses.get(input_filename)
        program_output = open(output_filename, 'w')
        program_output.write('{}\n'.format(file_container.get('header').get('line')))
        for linenum in sorted(file_container, key=int):
            entry = system_responses.get(input_filename).get(str(linenum))
            if not entry.get('valid'):
                logger.record_event('EXPECTING_VALID_ENTRY', entry.get('where'))
                continue
            if entry.get('passes_filter'):
                program_output.write(entry.__str__())
        program_output.close()
    logger.record_event('DEFAULT_INFO', 'filtering finished')
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Align system and gold clusters")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('-a', '--alpha', type=float, default=0.9, help='Specify the type similarity threshold (default: %(default)s)')
    parser.add_argument('-c', '--cache', default=None, help='Specify the qnode type similarity cache (default: %(default)s)')
    parser.add_argument('-i', '--iou_thresholds',
                        default='eng:image:0.9,eng:text:0.9,eng:video:0.9,rus:image:0.9,rus:text:0.9,rus:video:0.9,spa:image:0.9,spa:text:0.9,spa:video:0.9,ukr:image:0.9,ukr:text:0.9,ukr:video:0.9',
                        help='Specify comma-separted list of document, modality, and the respective iou threshold separated by colon (default: %(default)s)')
    parser.add_argument('-k', '--kgtk_api', default=None, help='Specify the URL of kgtk-similarity or leave it None (default: %(default)s)')
    parser.add_argument('-L', '--lock', default='/data/AUX-data/kgtk.lock', help='Specify the lock file (default: %(default)s)')
    parser.add_argument('-n', '--near_neighbor_similarity_value', type=float, default=0.9, help='Specify the similarity score to be used when the qnodes were declared to be near-neighbors (default: %(default)s)')
    parser.add_argument('-s', '--similarity_types', default='complex,transe,text,class,jc,topsim', help='Specify the comma-separated list of similarity types to be used by kgtk-similarity (default: %(default)s)')
    parser.add_argument('-w', '--wait', type=int, default=10, help='Specify the seconds to wait before checking if the lock can be acquired (default: %(default)s)')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('encodings', type=str, help='File containing list of encoding to modality mappings')
    parser.add_argument('core_documents', type=str, help='File containing list of core documents to be included in the pool')
    parser.add_argument('parent_children', type=str, help='DocumentID to DocumentElementID mappings file')
    parser.add_argument('sentence_boundaries', type=str, help='File containing sentence boundaries')
    parser.add_argument('image_boundaries', type=str, help='File containing image bounding boxes')
    parser.add_argument('keyframe_boundaries', type=str, help='File containing keyframe bounding boxes')
    parser.add_argument('video_boundaries', type=str, help='File containing length of videos')
    parser.add_argument('taggable_ldc_ontology', type=str, help='File containing list of LDC types selected for exhaustive TA1 annotation')
    parser.add_argument('overlay', type=str, help='The JSON file contain DWD overlay')
    parser.add_argument('gold', type=str, help='Directory containing gold responses')
    parser.add_argument('runid', type=str, help='Run ID of the system being scored')
    parser.add_argument('input', type=str, help='Directory containing system responses')
    parser.add_argument('similarities', type=str, help='Directory to which similarities should be written')
    parser.add_argument('alignment', type=str, help='Directory to which alignment should be written')
    parser.add_argument('output', type=str, help='Directory to which filtered responses should be written')
    args = parser.parse_args()
    check_path(args)
    filter_responses(args)