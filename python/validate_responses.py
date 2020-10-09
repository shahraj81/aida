"""
AIDA main script for validating responses
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "6 August 2020"

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

def validate_responses(args):
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

    responses = ResponseSet(logger, ontology_type_mappings, slot_mappings, document_mappings, document_boundaries, args.input, args.runid, args.task)
    responses.write_valid_responses(args.output)
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Align system and gold clusters")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('-t', '--task', default='task1', choices=['task1', 'task2'], help='Specify task1 or task2 (default: %(default)s)')
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
    parser.add_argument('runid', type=str, help='Run ID of the system being scored')
    parser.add_argument('input', type=str, help='Directory containing system responses.')
    parser.add_argument('output', type=str, help='Directory containing valid responses.')
    args = parser.parse_args()
    check_path(args)
    validate_responses(args)