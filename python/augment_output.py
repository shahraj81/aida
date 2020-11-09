"""
AIDA script for augmenting SPARQL output.
"""
from aida.file_handler import FileHandler

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "9 November 2020"

from aida.logger import Logger
from aida.object import Object

import argparse
import os
import sys
import traceback
import re
import textwrap

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

class Merge(Object):
    """
    Merge system output from different SPARQL sub-queries
    """

    def __init__(self, log_filename, log_specifications, task, input_dir, output_dir):
        check_for_paths_existance([log_filename,
                                   log_specifications,
                                   input_dir])
        check_for_paths_non_existance([output_dir])
        self.log_filename = log_filename
        self.log_specification = log_specifications
        self.task = task
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.logger = Logger(self.get('log_filename'),
                        self.get('log_specification'),
                        sys.argv)

    def merge_files(self, input_files, output_file):
        print('--merging ...')
        print('--input:{}'.format('\n'.join(input_files)))
        print('--output:{}'.format(output_file))
        header = None
        fhs = {}
        for filename_with_path in input_files:
            fh = FileHandler(self.get('logger'), filename_with_path, encoding='utf-8')
            if header is None:
                header = fh.get('header').get('line').strip()
            if header != fh.get('header').get('line').strip():
                self.record_event('DEFAULT_CRITICAL_ERROR', 'Input file headers do not match')
            fhs[filename_with_path] = fh
        with open(output_file, 'w', encoding='utf-8') as program_output:
            program_output.write('{header}\n'.format(header=header))
            for filename_with_path in fhs:
                fh = fhs[filename_with_path]
                for entry in fh:
                    program_output.write('{line}'.format(line=entry.get('line')))

    def merge_sparql_output(self):
        method_name = 'merge_{task}_sparql_output'.format(task=self.get('task'))
        method = self.get_method(method_name)
        if method is None:
            self.record_event('UNDEFINED_METHOD', method_name)
        return method()

    def merge_task1_sparql_output(self):
        self.record_event('DEFAULT_INFO', 'Nothing to do.')

    def merge_task2_sparql_output(self):
        self.record_event('DEFAULT_INFO', 'Nothing to do.')

    def merge_task3_sparql_output(self):
        os.mkdir(self.get('output_dir'))
        directories = []
        for root, dirs, files in os.walk(self.get('input_dir')):
            directories.extend([os.path.join(root, dir) for dir in dirs if dir.endswith('.ttl')])

        for directory in directories:
            output_directory = directory.replace(self.get('input_dir'), self.get('output_dir'))
            if not os.path.exists(output_directory):
                os.mkdir(output_directory)
            input_file1 = '{i}/AIDA_P2_TA3_GR_0001A.rq.tsv'.format(i=directory)
            input_file2 = '{i}/AIDA_P2_TA3_GR_0001B.rq.tsv'.format(i=directory)
            output_file = '{o}/AIDA_P2_TA3_GR_0001.rq.tsv'.format(o=output_directory)
            self.merge_files([input_file1, input_file2], output_file)

            input_file = '{i}/AIDA_P2_TA3_TM_0001.rq.tsv'.format(i=directory)
            output_file = '{o}/AIDA_P2_TA3_TM_0001.rq.tsv'.format(o=directory.replace(self.get('input_dir'), self.get('output_dir')))
            self.merge_files([input_file], output_file)

    def __call__(self):
        self.merge_sparql_output()

    @classmethod
    def add_arguments(myclass, parser):
        parser.add_argument('-l', '--log_filename', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
        parser.add_argument('log_specifications', type=str, help='File containing error specifications')
        parser.add_argument('input_dir', type=str, help='Input directory')
        parser.add_argument('output_dir', type=str, help='Output directory')
        parser.add_argument('-t', '--task', default='task1', choices=['task1', 'task2', 'task3'], help='Specify task1 or task2 or task3 (default: %(default)s)')
        parser.set_defaults(myclass=myclass)
        return parser

myclasses = [
    Merge,
    ]

def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog='augment_output',
                                description='Augment SPARQL output')
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