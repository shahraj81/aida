"""
AIDA main script to clean SPARQL output
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "13 June 2020"

from aida.logger import Logger

import argparse
import os
import sys
import re

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_for_paths_existance(args):
    for path in [args.log_specifications, args.input]:
        if not os.path.exists(path):
            print('Error: Path {} does not exist'.format(path))
            exit(ERROR_EXIT_CODE)
    for path in [args.output]:
        if os.path.exists(path):
            print('Error: Path {} already exists'.format(path))
            exit(ERROR_EXIT_CODE)

def clean_a_sparql_output_file(logger, input_filename, output_filename):
    logger.record_event('DEFAULT_INFO', 'cleaning: {}, output: {}'.format(input_filename, output_filename))
    input_fh = open(input_filename, encoding='utf-8')
    output_fh = open(output_filename, 'w', encoding='utf-8')
    for input_line in input_fh.readlines():
        elements = input_line.rstrip('\r\n').split('\t')
        clean_elements = []
        for element in elements:
            match = re.search("<https://.*?#(.*?)>", element)
            if match:
                matched_str = match.group(1)
                clean_elements.append(matched_str)
            else:
                clean_elements.append(element)
        output_line = '\t'.join(clean_elements)
        output_fh.write('{}\n'.format(output_line))
    input_fh.close()
    output_fh.close()

def clean_sparql_output(args):
    logger = Logger(args.log, args.log_specifications, sys.argv)
    filenames = []
    for root, dirs, files in os.walk(args.input):
        filenames.extend([os.path.join(root, file) for file in files if file.endswith('.tsv')])
    os.mkdir(args.output)
    for input_filename in filenames:
        output_root = args.output
        output_basename = os.path.basename(input_filename)
        output_subdir = input_filename.replace(args.input, '').replace(output_basename, '').rstrip('/').lstrip('/')
        output_directory = '{}/{}'.format(output_root, output_subdir)
        output_filename = '{}/{}'.format(output_directory, output_basename)
        os.makedirs(output_directory, exist_ok=True)
        clean_a_sparql_output_file(logger, input_filename, output_filename)
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Clean the SPARQL output")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('input', type=str, help='Input directory')
    parser.add_argument('output', type=str, help='Output directory')
    args = parser.parse_args()
    check_for_paths_existance(args)
    clean_sparql_output(args)