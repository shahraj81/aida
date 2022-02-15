"""
This script for verifying if the run directory has the right structure
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "1.0.0.1"
__date__    = "14 February 2022"

from aida.logger import Logger
from aida.object import Object
from aida.ta3_queryset import TA3QuerySet

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
                 args.queries,
                 args.output
                 ])
    check_for_paths_non_existance([])

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

class Task3(Object):
    """
    Class for verifying the directory structure for Task3 output.
    """
    def __init__(self, log, log_specifications, queries, output):
        check_for_paths_existance([
                 log_specifications,
                 queries,
                 output
                 ])
        check_for_paths_non_existance([])
        self.log_filename = log
        self.log_specifications = log_specifications
        self.queries = queries
        self.output = output
        self.logger = Logger(self.get('log_filename'),
                        self.get('log_specifications'),
                        sys.argv)

    def verify(self, queries_dir, runs_directory):
        logger = self.get('logger')
        ta3_queries = TA3QuerySet(logger, queries_dir)
        for condition_name in os.listdir(runs_directory):
            condition_directory = os.path.join(runs_directory, condition_name)
            if condition_name not in ta3_queries.get('conditions'):
                logger.record_event('UNEXPECTED_ITEM', 'directory', condition_name, runs_directory)
                return ERROR_EXIT_CODE
            condition = ta3_queries.get('conditions').get(condition_name)
            query_claim_frames = condition.get('query_claim_frames')
            field_name = 'query_claim_frames' if query_claim_frames is not None else 'topics'
            for field_value in os.listdir(condition_directory):
                query_directory = os.path.join(condition_directory, field_value)
                if field_value not in condition.get(field_name):
                    logger.record_event('UNEXPECTED_ITEM', field_name[:-1], field_value, condition_directory)
                    return ERROR_EXIT_CODE
                for filename in os.listdir(query_directory):
                    if not (filename.endswith('.ttl') or filename == '{}.ranking.tsv'.format(field_value)):
                        logger.record_event('UNEXPECTED_ITEM', 'filename', filename, query_directory)
                        return ERROR_EXIT_CODE
        return ALLOK_EXIT_CODE

    def __call__(self):
        retVal = self.verify(self.get('queries'), self.get('output'))
        message = 'No errors encountered.' if retVal == ALLOK_EXIT_CODE else 'Error(s) encountered.'
        print(message)
        exit(retVal)

    @classmethod
    def add_arguments(myclass, parser):
        parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
        parser.add_argument('log_specifications', type=str, help='File containing error specifications')
        parser.add_argument('queries', type=str, help='Specify the input directory containing queries')
        parser.add_argument('output', type=str, help='Specify the TA3 run directory whose structure needs to be verified')
        parser.set_defaults(myclass=myclass)
        return parser

myclasses = [
    Task3
    ]

def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog='verify_output_directory_structure',
                                description='Verify the output directory structure')
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