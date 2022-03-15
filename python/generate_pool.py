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
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.logger import Logger
from aida.object import Object
from aida.task2_pool import Task2Pool
from aida.task3_pool import Task3Pool
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

def check_paths(args):
    check_for_paths_existance([
                 args.log_specifications,
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
    check_for_paths_non_existance(['{}-{}'.format(args.output, args.batch_id)])

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

class Task2(Object):
    """
    Class representing Task2 pooler.
    """
    def __init__(self, log, batch_id, kit_size, previous_pools, log_specifications, encodings, core_documents, parent_children, sentence_boundaries, image_boundaries, keyframe_boundaries, video_boundaries, runs_to_pool, queries, input_dir, output_dir):
        check_for_paths_existance([
                 log_specifications,
                 encodings,
                 core_documents,
                 parent_children,
                 sentence_boundaries,
                 image_boundaries,
                 keyframe_boundaries,
                 video_boundaries,
                 runs_to_pool,
                 queries,
                 input_dir
                 ])
        check_for_paths_non_existance(['{}-{}'.format(output_dir, self.get('batch_id'))])
        self.log_filename = log
        self.batch_id = batch_id
        self.kit_size = kit_size
        self.previous_pools = previous_pools
        self.log_specifications = log_specifications
        self.encodings = encodings
        self.core_documents = core_documents
        self.parent_children = parent_children
        self.sentence_boundaries = sentence_boundaries
        self.image_boundaries = image_boundaries
        self.keyframe_boundaries = keyframe_boundaries
        self.video_boundaries = video_boundaries
        self.runs_to_pool = runs_to_pool
        self.queries = queries
        self.input = input_dir
        self.output = output_dir
        self.logger = Logger(self.get('log_filename'),
                        self.get('log_specifications'),
                        sys.argv)

    def __call__(self):
        logger = self.get('logger')
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
        pool = Task2Pool(logger,
                         document_mappings=document_mappings,
                         document_boundaries=document_boundaries,
                         runs_to_pool_file=self.get('runs_to_pool'),
                         queries_to_pool_file=self.get('queries'),
                         max_kit_size=self.get('kit_size'),
                         batch_id=self.get('batch_id'),
                         input_dir=self.get('input'),
                         previous_pools=self.get('previous_pools'))
        pool.write_output('{}-{}'.format(self.get('output'), self.get('batch_id')))
        exit(ALLOK_EXIT_CODE)

    @classmethod
    def add_arguments(myclass, parser):
        parser.add_argument('-b', '--batch_id', default='BATCH1', help='Specify the batch ID (default: %(default)s)')
        parser.add_argument('-k', '--kit_size', default=200, type=int, help='Specify the maximum number of entries in a kit (default: %(default)s)')
        parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
        parser.add_argument('-p', '--previous_pools', help='Specify comma-separated list of the directories containing previous pool(s), if any')
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
        parser.add_argument('log_specifications', type=str, help='File containing error specifications')
        parser.add_argument('encodings', type=str, help='File containing list of encoding to modality mappings')
        parser.add_argument('core_documents', type=str, help='File containing list of core documents')
        parser.add_argument('parent_children', type=str, help='DocumentID to DocumentElementID mappings file')
        parser.add_argument('sentence_boundaries', type=str, help='File containing sentence boundaries')
        parser.add_argument('image_boundaries', type=str, help='File containing image bounding boxes')
        parser.add_argument('keyframe_boundaries', type=str, help='File containing keyframe bounding boxes')
        parser.add_argument('video_boundaries', type=str, help='File containing length of videos')
        parser.add_argument('runs_to_pool', type=str, help='File containing IDs of runs to be included in the pool')
        parser.add_argument('queries', type=str, help='File containing query-specific number of clusters and number of documents per cluster to be included in the pool (queries.txt file produced by queries generator)')
        parser.add_argument('input_dir', type=str, help='Directory containing all the runs (this directory contains the output of AIDA evaluation docker when applied to the runs)')
        parser.add_argument('output_dir', type=str, help='Specify the directory (prefix) to which the output should be written')
        parser.set_defaults(myclass=myclass)
        return parser

class Task3(Object):
    """
    Class representing Task3 pooler.
    """
    def __init__(self, log, batch_id, previous_pools, log_specifications, queries_to_pool, runs_to_pool, input_dir, output_dir):
        check_for_paths_existance([
                 log_specifications,
                 runs_to_pool,
                 queries_to_pool,
                 input_dir
                 ])
        check_for_paths_non_existance(['{}-{}'.format(output_dir, self.get('batch_id'))])
        self.log_filename = log
        self.batch_id = batch_id
        self.previous_pools = previous_pools
        self.log_specifications = log_specifications
        self.runs_to_pool = runs_to_pool
        self.queries_to_pool = queries_to_pool
        self.input = input_dir
        self.output = output_dir
        self.logger = Logger(self.get('log_filename'),
                        self.get('log_specifications'),
                        sys.argv)

    def __call__(self):
        logger = self.get('logger')
        pool = Task3Pool(logger,
                         runs_to_pool_file=self.get('runs_to_pool'),
                         queries_to_pool_file=self.get('queries_to_pool'),
                         batch_id=self.get('batch_id'),
                         input_dir=self.get('input'),
                         previous_pools=self.get('previous_pools'),
                         output_dir=self.get('output'))
        pool.write_output('{}-{}'.format(self.get('output'), self.get('batch_id')))
        exit(ALLOK_EXIT_CODE)

    @classmethod
    def add_arguments(myclass, parser):
        parser.add_argument('-b', '--batch_id', default='BATCH1', help='Specify the batch ID (default: %(default)s)')
        parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
        parser.add_argument('-p', '--previous_pools', help='Specify comma-separated list of the directories containing previous pool(s), if any')
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
        parser.add_argument('log_specifications', type=str, help='File containing error specifications')
        parser.add_argument('runs_to_pool', type=str, help='File containing IDs of runs to be included in the pool')
        parser.add_argument('queries_to_pool', type=str, help='File containing list of (tab-separated) condition-query pairs to be included in the pool')
        parser.add_argument('input_dir', type=str, help='Directory containing all the runs (this directory contains the output of AIDA evaluation docker when applied to the runs)')
        parser.add_argument('output_dir', type=str, help='Specify the directory (prefix) to which the output should be written')
        parser.set_defaults(myclass=myclass)
        return parser

myclasses = [
    Task2,
    Task3
    ]

def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog='generate_pool',
                                description='Generate pool')
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