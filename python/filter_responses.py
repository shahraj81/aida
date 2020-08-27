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
from aida.response_set import ResponseSet
from aida.encodings import Encodings
from aida.core_documents import CoreDocuments
from aida.document_mappings import DocumentMappings
from aida.text_boundaries import TextBoundaries
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.video_boundaries import VideoBoundaries
from aida.ontology_type_mappings import OntologyTypeMappings
from aida.slot_mappings import SlotMappings
from aida.annotated_regions import AnnotatedRegions
from aida.utility import spanstring_to_object, get_expanded_types

import argparse
import os
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_path(args):
    check_for_paths_existance([args.log_specifications,
                               args.ontology_type_mappings,
                               args.slot_mappings,
                               args.encodings,
                               args.core_documents,
                               args.parent_children,
                               args.sentence_boundaries,
                               args.image_boundaries,
                               args.keyframe_boundaries,
                               args.video_boundaries,
                               args.regions,
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

    ontology_type_mappings = OntologyTypeMappings(logger, args.ontology_type_mappings)
    slot_mappings = SlotMappings(logger, args.slot_mappings)
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

    responses = ResponseSet(logger, ontology_type_mappings, slot_mappings, document_mappings, document_boundaries, args.input, args.runid)
    annotated_regions = AnnotatedRegions(logger, document_mappings, document_boundaries, args.regions)
    run_filter_on_all_responses(responses, annotated_regions, document_mappings, document_boundaries)
    
    os.mkdir(args.output)
    for input_filename in responses:
        output_filename = input_filename.replace(responses.get('path'), args.output)
        dirname = os.path.dirname(output_filename)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        output_fh = open(output_filename, 'w')
        header_printed = False
        for linenum in sorted(responses.get(input_filename), key=int):
            entry = responses.get(input_filename).get(str(linenum))
            if not header_printed:
                output_fh.write('{}\n'.format(entry.get('header').get('line')))
                header_printed = True
            if not entry.get('valid'):
                logger.record_event('EXPECTING_VALID_ENTRY', entry.get('where'))
                continue
            if entry.get('passes_filter'):
                output_fh.write(entry.__str__())
        output_fh.close()
    exit(ALLOK_EXIT_CODE)

def get_mention(entry, document_mappings, document_boundaries):
    logger = entry.get('logger')
    where = entry.get('where')
    span_string = entry.get('mention_span_text')
    mention = spanstring_to_object(logger, span_string, where)
    mention.set('ID', span_string)
    mention.set('span_string', span_string)
    mention.set('t_cv', entry.get('type_statement_confidence'))
    mention.set('cm_cv', entry.get('cluster_membership_confidence'))
    mention.set('j_cv', entry.get('mention_type_justification_confidence'))
    mention.set('modality', document_mappings.get('modality', mention.get('document_element_id')))
    boundaries_key = 'keyframe' if mention.get('keyframe_id') else mention.get('modality')
    document_element_or_keyframe_id = mention.get('keyframe_id') if mention.get('keyframe_id') else mention.get('document_element_id')
    mention.set('boundary', document_boundaries.get(boundaries_key).get(document_element_or_keyframe_id))
    return mention

def run_filter_on_all_responses(responses, annotated_regions, document_mappings, document_boundaries):
    filtered_clusters = {}
    # Note: the order of the following is critical.
    # Running on AIDA_PHASE2_TASK1_CM_RESPONSE creates the lookup table filtered_clusters later
    # used by AIDA_PHASE2_TASK1_AM_RESPONSE and AIDA_PHASE2_TASK1_TM_RESPONSE
    for schema_name in ['AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK1_TM_RESPONSE']:
        run_filter_on_all_schema_responses(responses, schema_name, filtered_clusters, annotated_regions, document_mappings, document_boundaries)

def run_filter_on_all_schema_responses(responses, schema_name, filtered_clusters, annotated_regions, document_mappings, document_boundaries):
    for input_filename in responses:
        for linenum in responses.get(input_filename):
            entry = responses.get(input_filename).get(str(linenum))
            if entry.get('schema').get('name') == schema_name:
                run_filter_on_entry(entry,
                                    schema_name,
                                    filtered_clusters,
                                    annotated_regions,
                                    document_mappings,
                                    document_boundaries)

def run_filter_on_entry(entry, schema_name, filtered_clusters, annotated_regions, document_mappings, document_boundaries):
    logger = entry.get('logger')

    if schema_name not in ['AIDA_PHASE2_TASK1_AM_RESPONSE', 'AIDA_PHASE2_TASK1_CM_RESPONSE', 'AIDA_PHASE2_TASK1_TM_RESPONSE']:
        logger.record_event('DEFAULT_CRITICAL_ERROR', 'Unexpected schema name: {}'.format(schema_name), logger.get('code_location'))

    passes_filter = False

    if schema_name == 'AIDA_PHASE2_TASK1_AM_RESPONSE':
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
                    logger.record_event('DEFAULT_INFO', 'Entry fails the filter due to cluster: {}'.format(cluster_id), entry.get('where'))
                    break
            else:
                logger.record_event('MISSING_ENTRY_IN_LOOKUP_ERROR', key, 'filtered_clusters', logger.get('code_location'))

    elif schema_name == 'AIDA_PHASE2_TASK1_CM_RESPONSE':
        mention = get_mention(entry, document_mappings, document_boundaries)
        key = '{}:{}'.format(entry.get('kb_document_id'), entry.get('cluster').get('ID'))
        if key not in filtered_clusters:
            filtered_clusters[key] = False
        if annotated_regions.contains(mention, get_expanded_types(entry.get('metatype'), entry.get('cluster_type'))):
            passes_filter = True
            filtered_clusters[key] = True
        else:
            logger.record_event('MENTION_NOT_ANNOTATED', mention.get('span_string'), entry.get('where'))

    elif schema_name == 'AIDA_PHASE2_TASK1_TM_RESPONSE':
        cluster_id = entry.get('cluster').get('ID')
        key = '{}:{}'.format(entry.get('kb_document_id'), cluster_id)
        if key in filtered_clusters:
            passes_filter = filtered_clusters[key]
            if not passes_filter:
                logger.record_event('CLUSTER_NOT_ANNOTATED', cluster_id, entry.get('where'))
        else:
            logger.record_event('MISSING_ENTRY_IN_LOOKUP_ERROR', key, 'filtered_clusters', logger.get('code_location'))

    entry.set('passes_filter', passes_filter)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Align system and gold clusters")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('ontology_type_mappings', type=str, help='File containing all the types in the ontology')
    parser.add_argument('slot_mappings', type=str, help='File containing slot mappings')
    parser.add_argument('encodings', type=str, help='File containing list of encoding to modality mappings')
    parser.add_argument('core_documents', type=str, help='File containing list of core documents to be included in the pool')
    parser.add_argument('parent_children', type=str, help='DocumentID to DocumentElementID mappings file')
    parser.add_argument('sentence_boundaries', type=str, help='File containing sentence boundaries')
    parser.add_argument('image_boundaries', type=str, help='File containing image bounding boxes')
    parser.add_argument('keyframe_boundaries', type=str, help='File containing keyframe bounding boxes')
    parser.add_argument('video_boundaries', type=str, help='File containing length of videos')
    parser.add_argument('regions', type=str, help='File containing annotated regions information')
    parser.add_argument('runid', type=str, help='Run ID of the system being scored')
    parser.add_argument('input', type=str, help='Directory containing system responses.')
    parser.add_argument('output', type=str, help='Directory containing filtered responses.')
    args = parser.parse_args()
    check_path(args)
    filter_responses(args)