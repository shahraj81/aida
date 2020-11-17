"""
Main AIDA scoring script.
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
from aida.object import Object
from aida.ontology_type_mappings import OntologyTypeMappings
from aida.response_set import ResponseSet
from aida.text_boundaries import TextBoundaries
from aida.video_boundaries import VideoBoundaries

import argparse
import os
import re
import sys
import textwrap
import traceback

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

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

class Task1(Object):
    """
    Class representing Task1 scorer.
    """
    def __init__(self, log, separator, runid, log_specifications, ontology_type_mappings, slot_mappings, encodings, core_documents, parent_children, sentence_boundaries, image_boundaries, keyframe_boundaries, video_boundaries, regions, gold, system, alignment, similarities, scores):
        check_for_paths_existance([
                 log_specifications,
                 ontology_type_mappings,
                 slot_mappings,
                 encodings,
                 core_documents,
                 parent_children,
                 sentence_boundaries,
                 image_boundaries,
                 keyframe_boundaries,
                 video_boundaries,
                 regions,
                 gold,
                 system,
                 alignment,
                 similarities
                 ])
        check_for_paths_non_existance([scores])
        self.log_filename = log
        self.separator = separator
        self.runid = runid
        self.log_specifications = log_specifications
        self.ontology_type_mappings = ontology_type_mappings
        self.slot_mappings = slot_mappings
        self.encodings = encodings
        self.core_documents = core_documents
        self.parent_children = parent_children
        self.sentence_boundaries = sentence_boundaries
        self.image_boundaries = image_boundaries
        self.keyframe_boundaries = keyframe_boundaries
        self.video_boundaries = video_boundaries
        self.regions = regions
        self.gold = gold
        self.system = system
        self.alignment = alignment
        self.similarities = similarities
        self.scores = scores
        self.logger = Logger(self.get('log_filename'),
                        self.get('log_specification'),
                        sys.argv)

    def __call__(self):
        logger = self.get('logger')
        ontology_type_mappings = OntologyTypeMappings(logger, self.get('ontology_type_mappings'))
        slot_mappings = SlotMappings(logger, self.get('slot_mappings'))
        document_mappings = DocumentMappings(logger,
                                             self.get('parent_children'),
                                             Encodings(logger, self.get('encodings')),
                                             CoreDocuments(logger, self.get('core_documents')))
        text_boundaries = TextBoundaries(logger, self.get('sentence_boundaries'))
        image_boundaries = ImageBoundaries(logger, self.get('image_boundaries'))
        video_boundaries = VideoBoundaries(logger, self.get('video_boundaries'))
        keyframe_boundaries = KeyFrameBoundaries(logger, self.get('keyframe_boundaries'))
        document_boundaries = {
            'text': text_boundaries,
            'image': image_boundaries,
            'keyframe': keyframe_boundaries,
            'video': video_boundaries
            }

        annotated_regions = AnnotatedRegions(logger, ontology_type_mappings, document_mappings, document_boundaries, self.get('regions'))

        gold_responses = ResponseSet(logger, ontology_type_mappings, slot_mappings, document_mappings, document_boundaries, self.get('gold'), 'gold')
        system_responses = ResponseSet(logger, ontology_type_mappings, slot_mappings, document_mappings, document_boundaries, self.get('system'), self.get('runid'))
        cluster_alignment = ClusterAlignment(logger, self.get('alignment'))
        cluster_self_similarities = ClusterSelfSimilarities(logger, self.get('similarities'))
        arguments = {
            'annotated_regions': annotated_regions,
            'gold_responses': gold_responses,
            'system_responses': system_responses,
            'cluster_alignment': cluster_alignment,
            'cluster_self_similarities': cluster_self_similarities,
            }
        scores = ScoresManager(logger, 'task1', arguments, self.get('separator'))
        scores.print_scores(self.get('scores'))
        exit(ALLOK_EXIT_CODE)

    @classmethod
    def add_arguments(myclass, parser):
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
        parser.set_defaults(myclass=myclass)
        return parser

myclasses = [
    Task1
    ]

def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog='score_submission',
                                description='Score an AIDA submission')
    subparser = parser.add_subparsers()
    subparsers = {}
    for myclass in myclasses:
        hyphened_name = re.sub('([A-Z])', r'-\1', myclass.__name__).lstrip('-').lower()
        help_text = myclass.__doc__.split('\n')[0]
        desc = textwrap.dedent(myclass.__doc__.rstrip())

        class_subparser = subparser.add_parser(hyphened_name,
                            help=help_text,
                            description=desc,
                            formatter_class=argparse.RawDescriptionHelpFormatter)
        myclass.add_arguments(class_subparser)
        subparsers[myclass] = class_subparser

    namespace = vars(parser.parse_args(args))
    try:
        myclass = namespace.pop('myclass')
    except KeyError:
        parser.print_help()
        return
    try:
        obj = myclass(**namespace)
    except ValueError as e:
        subparsers[myclass].error(str(e) + "\n" + traceback.format_exc())
    result = obj()
    if result is not None:
        print(result)

if __name__ == '__main__':
    main()