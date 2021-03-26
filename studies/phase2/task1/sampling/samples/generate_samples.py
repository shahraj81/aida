"""
AIDA main script generating samples for the study.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "26 March 2021"

import random
import argparse
import os

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_path(args):
    check_for_paths_existance([args.input])
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

def read_input(filename):
    core_docs = set()
    with open(filename) as fh:
        header = None
        for line in fh.readlines():
            if header is None:
                header = line.strip()
            else:
                core_docs.add(line.strip())
    return header, sorted(list(core_docs))

def write_output(output_directory, header, samples, ldc_package_id):
    os.mkdir(output_directory)
    for sample_size in samples:
        for i in samples[sample_size]:
            output_filename = os.path.join(output_directory,
                                           '{ldc_package_id}.coredocs-p{sample_size}-{i}.txt'.format(ldc_package_id=ldc_package_id,
                                                                                                     sample_size=sample_size,
                                                                                                     i=i if i >= 10 else '0{}'.format(i)))
            with open(output_filename, 'w') as program_output:
                program_output.write('{}\n'.format(header))
                for docid in sorted(samples[sample_size][i]):
                    program_output.write('{}\n'.format(docid))

def generate_samples(args):
    header, core_docs = read_input(args.input)
    samples = {}
    for sample_size in args.sizes.split(','):
        samples[sample_size] = {}
        k = round(len(core_docs) * float(sample_size) / 100)
        for i in range(args.count):
            samples[sample_size][i] = random.sample(core_docs, k)
    write_output(args.output, header, samples, args.ldc_package_id)
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate samples for the study.")
    parser.add_argument('-l', '--ldc_package_id', default='LDC2020R17', help='Specify the LDC Package ID to be used as a prefix of the output filenames (default: %(default)s).')
    parser.add_argument('input', type=str, help='File containing list of core documents from which samples are drawn.')
    parser.add_argument('sizes', type=str, help='Comma-separated list of sample sizes in percentage, e.g. use 90 for a 90% sample.')
    parser.add_argument('count', type=int, help='Specify the number of samples of a particular size should be generated.')
    parser.add_argument('output', type=str, help='Specify a directory to which the output samples should be written.')
    args = parser.parse_args()
    check_path(args)
    generate_samples(args)