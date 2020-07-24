"""
AIDA main script for aligning clusters
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 July 2020"

from aida.logger import Logger
from aida.clusters import Clusters

import argparse
import os
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_path(args):
    check_for_paths_existance(args)
    check_for_paths_non_existance(args)

def check_for_paths_existance(args):
    for path in [args.log_specifications_filename, 
                 args.gold_mentions,
                 args.gold_edges,
                 args.system_mentions,
                 args.system_edges]:
        if not os.path.exists(path):
            print('Error: Path {} does not exist'.format(path))
            exit(ERROR_EXIT_CODE)

def check_for_paths_non_existance(args):
    for path in [args.output, 
                 args.similarities]:
        if os.path.exists(path):
            print('Error: Path {} exists'.format(path))
            exit(ERROR_EXIT_CODE)

def align_clusters(args):
    logger = Logger(args.log, args.log_specifications_filename, sys.argv)
    clusters = Clusters(logger, args.gold_mentions, args.gold_edges, args.system_mentions, args.system_edges)
    clusters.print_similarities(args.similarities)
    clusters.print_alignment(args.output)
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Align system and gold clusters")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('log_specifications_filename', type=str, help='File containing error specifications')
    parser.add_argument('gold_mentions', type=str, help='File containing gold clusters, corresponding mentions and types information.')
    parser.add_argument('gold_edges', type=str, help='File containing information about gold edges.')
    parser.add_argument('system_mentions', type=str, help='File containing system clusters, corresponding mentions and types information.')
    parser.add_argument('system_edges', type=str, help='File containing information about system edges.')
    parser.add_argument('similarities', type=str, help='Specify a file to which the similarity information should be written.')
    parser.add_argument('output', type=str, help='Specify a file to which the alignment information should be written.')
    args = parser.parse_args()
    check_path(args)
    align_clusters(args)