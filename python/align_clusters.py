"""
AIDA main script for aligning clusters
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 July 2020"

from aida.logger import Logger
from aida.clusters import Clusters
from aida.encodings import Encodings
from aida.core_documents import CoreDocuments
from aida.document_mappings import DocumentMappings
from aida.text_boundaries import TextBoundaries
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.video_boundaries import VideoBoundaries
from aida.annotated_regions import AnnotatedRegions

import argparse
import os
import sys
import time

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_paths(args):
    check_for_paths_existance([args.log_specifications, args.gold, args.system])
    check_for_paths_non_existance([args.alignment, args.similarities])

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

def align_clusters(args):
    logger = Logger(args.log, args.log_specifications, sys.argv)

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

    annotated_regions = AnnotatedRegions(logger, document_mappings, document_boundaries, args.regions)

    thresholds = {
        'ENG': args.eng_iou_threshold,
        'SPA': args.spa_iou_threshold,
        'RUS': args.rus_iou_threshold,
        'image': args.image_iou_threshold,
        'video': args.video_iou_threshold
        }

    os.mkdir(args.similarities)
    os.mkdir(args.alignment)
    for entry in sorted(os.scandir(args.gold), key=str):
        if entry.is_dir() and entry.name.endswith('.ttl'):
            kb = entry.name
            document_id = kb.replace('.ttl', '')
            if not document_mappings.get('documents').get(document_id).get('is_core'):
                continue
            message = 'aligning clusters in {}'.format(entry.name)
            logger.record_event('DEFAULT_INFO', message)
            print('At {}: {}'.format(time.strftime("%m/%d/%Y %H:%M:%S", time.localtime()), message))

            gold_mentions = '{}/{}/AIDA_P2_TA1_CM_A0001.rq.tsv'.format(args.gold, kb)
            gold_edges = '{}/{}/AIDA_P2_TA1_AM_A0001.rq.tsv'.format(args.gold, kb)
            system_mentions = '{}/{}/AIDA_P2_TA1_CM_A0001.rq.tsv'.format(args.system, kb)
            system_edges = '{}/{}/AIDA_P2_TA1_AM_A0001.rq.tsv'.format(args.system, kb)

            gold_mentions = gold_mentions if os.path.exists(gold_mentions) else None
            gold_edges = gold_edges if os.path.exists(gold_edges) else None
            system_mentions = system_mentions if os.path.exists(system_mentions) else None
            system_edges = system_edges if os.path.exists(system_edges) else None

            similarities = '{}/{}.tab'.format(args.similarities, document_id)
            alignment = '{}/{}.tab'.format(args.alignment, document_id)
            check_for_paths_non_existance([similarities, alignment])
            clusters = Clusters(logger, document_mappings, document_boundaries, annotated_regions, gold_mentions, gold_edges, system_mentions, system_edges, thresholds)
            clusters.print_similarities(similarities)
            clusters.print_alignment(alignment)
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Align system and gold clusters")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('encodings', type=str, help='File containing list of encoding to modality mappings')
    parser.add_argument('core_documents', type=str, help='File containing list of core documents to be included in the pool')
    parser.add_argument('parent_children', type=str, help='DocumentID to DocumentElementID mappings file')
    parser.add_argument('sentence_boundaries', type=str, help='File containing sentence boundaries')
    parser.add_argument('image_boundaries', type=str, help='File containing image bounding boxes')
    parser.add_argument('keyframe_boundaries', type=str, help='File containing keyframe bounding boxes')
    parser.add_argument('video_boundaries', type=str, help='File containing length of videos')
    parser.add_argument('regions', type=str, help='File containing annotated regions information')
    parser.add_argument('eng_iou_threshold', type=float, help='English text IOU threshold for alignment')
    parser.add_argument('spa_iou_threshold', type=float, help='Spanish text IOU threshold for alignment')
    parser.add_argument('rus_iou_threshold', type=float, help='Russian text IOU threshold for alignment')
    parser.add_argument('image_iou_threshold', type=float, help='Image IOU threshold for alignment')
    parser.add_argument('video_iou_threshold', type=float, help='Video IOU threshold for alignment')
    parser.add_argument('gold', type=str, help='Directory containing gold information.')
    parser.add_argument('system', type=str, help='Directory containing system information.')
    parser.add_argument('similarities', type=str, help='Specify a directory to which the similarity information should be written.')
    parser.add_argument('alignment', type=str, help='Specify a directory to which the alignment information should be written.')
    args = parser.parse_args()
    check_paths(args)
    align_clusters(args)