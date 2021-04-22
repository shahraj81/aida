"""
AIDA main script for generating confidence intervals.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "5 March 2021"

from aida.confidence_intervals import ConfidenceIntervals
from aida.logger import Logger

import argparse
import os
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_paths(args):
    check_for_paths_existance([args.input])
    check_for_paths_non_existance([args.pretty_output, args.tab_output])

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

def generate_confidence_intervals(args):
    logger = Logger(args.log, args.log_specifications, sys.argv)
    if not args.input.endswith('.tab'):
        logger.record_event('DEFAULT_CRITICAL_ERROR', 'input filename should be a *.tab.') 
    aggregate = {}
    for element in args.aggregate.split(','):
        key, value = element.split(':')
        if key not in aggregate:
            aggregate[key] = []
        aggregate[key].append(value)
    confidence_interval = ConfidenceIntervals(logger,
                                              macro=args.macro,
                                              input=args.input,
                                              primary_key_col=args.primary_key,
                                              score=args.score,
                                              aggregate=aggregate,
                                              document_id_col=args.document_id,
                                              run_id_col=args.run_id,
                                              sizes=args.sizes,
                                              seed_value=args.seed)
    output = {'pretty': args.pretty_output, 'tab': args.tab_output}
    for output_format in output:
        fh = open(output[output_format], 'w')
        fh.write(confidence_interval.get('output', output_format))
        fh.close()
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Align system and gold clusters")
    parser.add_argument('-l', '--log', default='log.txt',
                        help='Specify a file to which log output should \
                              be redirected (default: %(default)s)')
    parser.add_argument('-m', '--macro', action='store_true',
                        help='Use macro averages')
    parser.add_argument('-s', '--seed', type=int, default=None,
                        help='Seed value for computing confidence interval (default: %(default)s).')
    parser.add_argument('-S', '--sizes', type=str, default='0.7,0.8,0.9,0.95',
                        help='Comma-separated list of confidence sizes (default: %(default)s).')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, 
                        help='Print version number and exit')
    parser.add_argument('log_specifications', type=str,
                        help='File containing error specifications')
    parser.add_argument('primary_key', type=str,
                        help='Comma-separated list of column-names to be used for \
                              generating confidence intervals. \
                              If provided, confidence intervals will be separately \
                              generated corresponding to each value of the primary_key \
                              in the input file. \
                              If left blank, confidence scores corresponding to all \
                              non-summary lines will be used for generating confidence \
                              intervals.')
    parser.add_argument('score', type=str,
                        help='Name of the column containing the scores to be used for \
                             generating confidence intervals.')
    parser.add_argument('aggregate', type=str,
                        help='Comma-separated list of colon-separated key-value pairs \
                              used to identify aggregate score lines in the input file.')
    parser.add_argument('document_id', type=str,
                        help='Name of the column containing DocID in the input file.')
    parser.add_argument('run_id', type=str,
                        help='Name of the column containing RunID in the input file.')
    parser.add_argument('input', type=str,
                        help='Specify the tab-separated input file.')
    parser.add_argument('pretty_output', type=str,
                        help='Specify the file to which the pretty-formatted output should be written.')
    parser.add_argument('tab_output', type=str,
                        help='Specify the file to which the tab-separated output should be written.')
    args = parser.parse_args()
    check_paths(args)
    generate_confidence_intervals(args)