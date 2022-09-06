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
                similarity = self.get('type_similarity', document_id, gold_cluster_id, system_cluster_id)
                similarity *= self.get('mention_similarity', document_id, gold_cluster_id, system_cluster_id)
                similarities.setdefault(gold_cluster_id, {})[system_cluster_id] = similarity
        return similarities

    def get_mention_similarity(self, document_id, gold_cluster_id, system_cluster_id):
        gold_cluster = self.get('cluster', 'gold', document_id, gold_cluster_id)
        system_cluster = self.get('cluster', 'system', document_id, system_cluster_id)
        mentions = {
            'gold':   gold_cluster.get('mentions').values(),
            'system': system_cluster.get('mentions').values()}

        mappings = {}
        for filetype in mentions:
            mappings[filetype] = {'id_to_index': {}, 'index_to_id': {}}
            index = 0;
            for mention in mentions[filetype]:
                mappings[filetype]['id_to_index'][mention.get('ID')] = index
                mappings[filetype]['index_to_id'][index] = mention.get('ID')
                index += 1

        similarities = {}
        for gold_mention in mentions['gold']:
            document_element_id = gold_mention.get('document_element_id')
            modality = self.get('document_mappings').get('modality', document_element_id)
            language = self.get('document_mappings').get('language', document_element_id)
            for system_mention in mentions['system']:
                if gold_mention.get('ID') not in similarities:
                    similarities[gold_mention.get('ID')] = {}
                iou = get_intersection_over_union(gold_mention, system_mention)
                iou = 0 if iou < self.get('threshold', modality, language) else iou
                similarities[gold_mention.get('ID')][system_mention.get('ID')] = iou

        gold_and_system_cluster_id = '::'.join([gold_cluster_id, system_cluster_id])
        self.record_alignment(document_id, 'mention', gold_and_system_cluster_id, similarities, mappings)
        alignment = self.get('alignments').get(document_id).get('mention').get(gold_and_system_cluster_id)

        similarity = 0
        for gold_mention_id in alignment.get('gold_to_system'):
            system_mention_id = alignment.get('gold_to_system').get(gold_mention_id).get('aligned_to')
            if similarities[gold_mention_id][system_mention_id] > 0:
                # lenient similarity computation
                if self.get('weighted') == 'no':
                    # total mentions
                    similarity += 1
                elif self.get('weighted') == 'yes':
                    # total iou
                    similarity += similarities[gold_mention_id][system_mention_id]
        return similarity

    def get_threshold(self, modality, language):
        return 0.1

    def get_type_similarity(self, document_id, gold_cluster_id, system_cluster_id):
        similarity = 0
        gold_cluster_types = self.get('cluster_types', 'gold', document_id, gold_cluster_id)
        system_cluster_types = self.get('cluster_types', 'system', document_id, system_cluster_id)
        if len(gold_cluster_types & system_cluster_types):
            similarity = 1.0
        else:
            for q1 in gold_cluster_types:
                for q2 in system_cluster_types:
                    isi_similarity_value = self.get('similarity').similarity(q1, q2)
                    if similarity < isi_similarity_value:
                        similarity = isi_similarity_value
        return similarity

    def align_clusters(self):
        mappings = {}
        for document_id in self.get('document_mappings').get('core_documents'):
            for filetype in ['gold', 'system']:
                mappings[filetype] = {'id_to_index': {}, 'index_to_id': {}}
                index = 0
                for cluster_id in sorted(self.get('responses').get(filetype).get('document_clusters').get(document_id) or []):
                    mappings[filetype]['id_to_index'][cluster_id] = index
                    mappings[filetype]['index_to_id'][index] = cluster_id
                    index += 1
            self.record_alignment(document_id, 'cluster', None, self.get('document_cluster_similarities', document_id), mappings)

    def init_alignment(self, document_id, cluster_or_mention, gold_and_system_cluster_id):
        alignment = {'gold_to_system': {}, 'system_to_gold': {}}
        if gold_and_system_cluster_id is None:
            if cluster_or_mention == 'cluster':
                self.get('alignments').setdefault(document_id, {})[cluster_or_mention] = alignment
            else:
                self.record_event('DEFAULT_CRITICAL_ERROR', 'cluster_id should be provided when aligning mentions')
        else:
            if cluster_or_mention == 'mention':
                self.get('alignments').setdefault(document_id, {}).setdefault(cluster_or_mention, {})[gold_and_system_cluster_id] = alignment
            else:
                self.record_event('DEFAULT_CRITICAL_ERROR', 'cluster_id should be None when aligning clusters')
        return alignment

    def is_aligned_to_a_gold_cluster(self, document_id, cluster_id):
        document_alignments = self.get('alignments').get(document_id)
        if document_alignments and cluster_id in document_alignments.get('cluster').get('system_to_gold'):
            return True
        return False

    def lookup_similarity(self, similarities, gold_item_id, system_item_id):
        if gold_item_id in similarities:
            if system_item_id in similarities.get(gold_item_id):
                return similarities.get(gold_item_id).get(system_item_id)
        return 0

    def record_alignment(self, document_id, cluster_or_mention, gold_and_system_cluster_id, similarities, mappings):
        # gold_and_system_cluster_id is needed when this method is called for recording mention alignment
        if len(similarities):
            alignment = self.init_alignment(document_id, cluster_or_mention, gold_and_system_cluster_id)
            cost_matrix = get_cost_matrix(similarities, mappings)
            for gold_item_index, system_item_index in Munkres().compute(cost_matrix):
                gold_item_id = mappings['gold']['index_to_id'][gold_item_index]
                system_item_id = mappings['system']['index_to_id'][system_item_index]
                similarity = self.lookup_similarity(similarities, gold_item_id, system_item_id)
                if similarity > 0:
                    alignment.get('gold_to_system')[gold_item_id] = {
                            'aligned_to': system_item_id,
                            'aligned_similarity': similarity
                        }
                    alignment.get('system_to_gold')[system_item_id] = {
                            'aligned_to': gold_item_id,
                            'aligned_similarity': similarity
                        }
                self.record_event('ALIGNMENT_INFO', document_id, cluster_or_mention, gold_and_system_cluster_id, gold_item_id, system_item_id, similarity)

class ResponseFilter(Object):
    def __init__(self, logger, alignment, similarity):
        super().__init__(logger)
        self.alignment = alignment
        self.similarity = similarity
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
    check_for_paths_non_existance([args.output])

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
    parser.add_argument('output', type=str, help='Directory to which filtered responses should be written')
    args = parser.parse_args()
    check_path(args)
    filter_responses(args)