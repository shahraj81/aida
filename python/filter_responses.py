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
from aida.text_boundaries import TextBoundaries
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.utility import get_cost_matrix, get_intersection_over_union
from aida.video_boundaries import VideoBoundaries
from generate_aif import LDCTypeToDWDNodeMapping

import argparse
import json
import os
import requests
import statistics
import sys

from munkres import Munkres

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

class AlignClusters(Object):
    def __init__(self, logger, document_mappings, similarity, responses):
        super().__init__(logger)
        self.document_mappings = document_mappings
        self.responses = responses
        self.similarity = similarity
        self.weighted = 'no'
        self.alignments = {}
        self.align_clusters()

    def get_cluster(self, gold_or_system, document_id, cluster_id):
        return self.get('responses').get(gold_or_system).get('document_clusters').get(document_id).get(cluster_id)

    def get_cluster_types(self, gold_or_system, document_id, cluster_id):
        cluster_types = set()
        for entry in self.get('responses').get(gold_or_system).get('document_clusters').get(document_id).get(cluster_id).get('entries').values():
            cluster_types.add(entry.get('cluster_type'))
        return cluster_types

    def get_document_cluster_similarities(self, document_id):
        similarities = {}
        for gold_cluster_id in sorted(self.get('responses').get('gold').get('document_clusters').get(document_id) or []):
            for system_cluster_id in sorted(self.get('responses').get('system').get('document_clusters').get(document_id)):
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
                iou = 0 if iou < self.get('threshold', modality, language) else iou
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

    def get_threshold(self, modality, language):
        return 0.1

    def get_type_similarity(self, document_id, system_or_gold1, cluster_id1, system_or_gold2, cluster_id2):
        similarity = 0
        cluster1_types = self.get('cluster_types', system_or_gold1, document_id, cluster_id1)
        cluster2_types = self.get('cluster_types', system_or_gold2, document_id, cluster_id2)
        if len(cluster1_types & cluster2_types):
            similarity = 1.0
        else:
            for q1 in cluster1_types:
                for q2 in cluster2_types:
                    isi_similarity_value = self.get('similarity').similarity(q1, q2)
                    if similarity < isi_similarity_value:
                        similarity = isi_similarity_value
        return similarity

    def align_clusters(self):
        mappings = {}
        filetype_to_clusternum_mapping = {
            'gold': 'cluster1',
            'system': 'cluster2'
            }
        for document_id in self.get('document_mappings').get('core_documents'):
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
        if len(similarities):
            alignment = self.init_alignment(document_id, cluster_or_mention, alignment_type, cluster1_and_cluster2_ids)
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
                    i1, i2 = alignment_type.split('_to_')
                    inverted_alignment_type = '{}_to_{}'.format(i2, i1)
                    if inverted_alignment_type != alignment_type:
                        alignment.setdefault(inverted_alignment_type, {})[item2_id] = {
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
        for document_id in self.get('alignments'):
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
        for document_id in self.get('alignments'):
            document_cluster_alignment = self.get('alignments').get(document_id).get('cluster').get('gold_to_system')
            with open(os.path.join(cluster_alignment_output_dir, '{}.tab'.format(document_id)), 'w') as cluster_alignment_program_output:
                with open(os.path.join(mention_alignment_output_dir, '{}.tab'.format(document_id)), 'w') as mention_alignment_program_output:
                    cluster_alignment_program_output.write(tostring(cluster_alignment_columns))
                    mention_alignment_program_output.write(tostring(mention_alignment_columns))
                    document_cluster_mention_alignment = self.get('alignments').get(document_id).get('mention')
                    for gold_cluster_id in sorted(document_cluster_alignment):
                        system_cluster_id = document_cluster_alignment.get(gold_cluster_id).get('aligned_to')
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

class ResponseFilter(Object):
    def __init__(self, logger, alignment, similarity):
        super().__init__(logger)
        self.alignment = alignment
        self.similarity = similarity
        self.alignments = {}
        self.filtered_clusters = {}

    def apply(self, responses):
        for schema_name in ['AIDA_PHASE3_TASK1_CM_RESPONSE', 'AIDA_PHASE3_TASK1_AM_RESPONSE', 'AIDA_PHASE3_TASK1_TM_RESPONSE']:
            for input_filename in responses:
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
    def __init__(self, logger, taggable_dwd_ontology, alpha, combine=statistics.mean, USE_ISI_SERVICE=False):
        super().__init__(logger)
        self.alpha = alpha
        self.combine = combine
        self.taggable_dwd_ontology = taggable_dwd_ontology
        self.SIMILARITY_TYPES = ['complex', 'transe', 'text', 'class', 'jc', 'topsim']
        self.USE_ISI_SERVICE = USE_ISI_SERVICE

    def similarity(self, q1, q2):
        if q1 == q2:
            return 1.0
        if self.get('taggable_dwd_ontology').get('is_synonym', q1, q2):
            return 1.0
        if self.get('USE_ISI_SERVICE'):
            return self.isi_similarity(q1, q2)
        return 0.0

    def isi_similarity(self, q1, q2):
        url = 'https://kgtk.isi.edu/similarity_api'
        similarity = []
        for similarity_type in self.get('SIMILARITY_TYPES'):
            resp = requests.get(url,
                                params={
                                    'q1': q1,
                                    'q2': q2,
                                    'similarity_type': similarity_type})
            json_struct = json.loads(resp.text)
            if 'error' not in json_struct:
                similarity.append(json_struct.get('similarity'))
        return self.get('combine')(similarity)

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
        self.synonyms = {}
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
    similarity = Similarity(logger, taggable_dwd_ontology, args.alpha)
    alignment = AlignClusters(logger, document_mappings, similarity, {'gold': gold_responses, 'system': system_responses})
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
    parser.add_argument('-a', '--alpha', default=0.5, help='Specify the type similarity threshold (default: %(default)s)')
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