"""
AIDA main scoring script
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "1.0.0.1"
__date__    = "17 August 2020"

from aida.annotated_regions import AnnotatedRegions
from aida.cluster_alignment import ClusterAlignment
from aida.cluster_self_similarities import ClusterSelfSimilarities
from aida.core_documents import CoreDocuments
from aida.document_mappings import DocumentMappings
from aida.encodings import Encodings
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.scores_manager import ScoresManager
from aida.slot_mappings import SlotMappings
from aida.logger import Logger
from aida.ontology_type_mappings import OntologyTypeMappings
from aida.response_set import ResponseSet
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
                 args.regions,
                 args.gold,
                 args.system,
                 args.alignment,
                 args.similarities
                 ])
    check_for_paths_non_existance([args.scores])

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

def score_submission(args):
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

    annotated_regions = AnnotatedRegions(logger, ontology_type_mappings, document_mappings, document_boundaries, args.regions)

    gold_responses = ResponseSet(logger, ontology_type_mappings, slot_mappings, document_mappings, document_boundaries, args.gold, 'gold')
    system_responses = ResponseSet(logger, ontology_type_mappings, slot_mappings, document_mappings, document_boundaries, args.system, args.runid)
    cluster_alignment = ClusterAlignment(logger, args.alignment)
    cluster_self_similarities = ClusterSelfSimilarities(logger, args.similarities)
    scores = ScoresManager(logger, annotated_regions, gold_responses, system_responses, cluster_alignment, cluster_self_similarities, args.separator)
    scores.print_scores(args.scores)
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Score the AIDA submission")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('-S', '--separator', default='pretty', choices=['pretty', 'tab', 'space'], help='Column separator for scorer output? (default: %(default)s)')
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
    parser.add_argument('regions', type=str, help='File containing annotated regions information')
    parser.add_argument('gold', type=str, help='Directory containing gold information.')
    parser.add_argument('system', type=str, help='Directory containing system information.')
    parser.add_argument('alignment', type=str, help='Directory containing alignment information.')
    parser.add_argument('similarities', type=str, help='Directory containing similarity information.')
    parser.add_argument('runid', type=str, help='Run ID of the system being scored')
    parser.add_argument('scores', type=str, help='Specify a directory to which the scores should be written.')
    args = parser.parse_args()
    check_paths(args)
    score_submission(args)