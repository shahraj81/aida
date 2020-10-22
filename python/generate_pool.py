"""
The script for generating a pool of task2 responses for assessment.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "1.0.0.1"
__date__    = "21 October 2020"

from aida.core_documents import CoreDocuments
from aida.document_mappings import DocumentMappings
from aida.encodings import Encodings
from aida.file_handler import FileHandler
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.logger import Logger
from aida.ontology_type_mappings import OntologyTypeMappings
from aida.response_set import ResponseSet
from aida.slot_mappings import SlotMappings
from aida.task2_pool import Task2Pool
from aida.text_boundaries import TextBoundaries
from aida.video_boundaries import VideoBoundaries

import argparse
import os
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_paths(args):
    check_for_paths_existance([
                 args.log_specifications,
                 args.ontology_type_mappings,
                 args.slot_mappings,
                 args.encodings,
                 args.core_documents,
                 args.parent_children,
                 args.sentence_boundaries,
                 args.image_boundaries,
                 args.keyframe_boundaries,
                 args.video_boundaries,
                 args.runs_to_pool,
                 args.input
                 ])
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

def main(args):
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

    pooling_specs = {}
    for entry in FileHandler(logger, args.queries):
        pooling_specs[entry.get('query_id')] = {'query_id'  : entry.get('query_id'),
                                                'entrypoint': entry.get('entrypoint'),
                                                'clusters'  : int(entry.get('clusters')),
                                                'documents' : int(entry.get('documents'))
                                                }

    pool = Task2Pool(logger, pooling_specs, document_mappings, document_boundaries)

    for entry in FileHandler(logger, args.runs_to_pool):
        run_id = entry.get('run_id')
        run_dir = '{input}/{run_id}/SPARQL-VALID-output'.format(input=args.input, run_id=run_id)
        responses = ResponseSet(logger, ontology_type_mappings, slot_mappings, document_mappings, document_boundaries, run_dir, run_id, 'task2')
        pool.add(responses)

    pool.write_output(args.output)

    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate a pool of task2 responses for assessment.")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-t', '--task', default='task1', choices=['task1', 'task2'], help='Specify task1 or task2 (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('ontology_type_mappings', type=str, help='File containing all the types in the ontology')
    parser.add_argument('slot_mappings', type=str, help='File containing slot mappings')
    parser.add_argument('encodings', type=str, help='File containing list of encoding to modality mappings')
    parser.add_argument('core_documents', type=str, help='File containing list of core documents')
    parser.add_argument('parent_children', type=str, help='DocumentID to DocumentElementID mappings file')
    parser.add_argument('sentence_boundaries', type=str, help='File containing sentence boundaries')
    parser.add_argument('image_boundaries', type=str, help='File containing image bounding boxes')
    parser.add_argument('keyframe_boundaries', type=str, help='File containing keyframe bounding boxes')
    parser.add_argument('video_boundaries', type=str, help='File containing length of videos')
    parser.add_argument('runs_to_pool', type=str, help='File containing IDs of runs to be included in the pool')
    parser.add_argument('queries', type=str, help='File containing query-specific number of clusters and number of documents per cluster to be included in the pool (queries.txt file produced by queries generator)')
    parser.add_argument('input', type=str, help='Directory containing all the runs (this directory contains the output of AIDA evaluation docker when applied to the runs)')
    parser.add_argument('output', type=str, help='Specify a directory to which the output should be written')
    args = parser.parse_args()
    check_paths(args)
    main(args)