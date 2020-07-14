"""
AIDA main script for aligning clusters
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "14 July 2020"


from aida.logger import Logger
from aida.file_handler import FileHandler
from aida.utility import parse_cv
from munkres import Munkres

import argparse
import os
import sys
import random

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_for_paths_existance(args):
    for path in [args.log_specifications_filename, 
                 args.gold_filename,
                 args.system_filename]:
        if not os.path.exists(path):
            print('Error: Path {} does not exist'.format(path))
            exit(ERROR_EXIT_CODE)

def get_similarity(gold_mentions, system_mentions, strategy):
    method_name = 'get_{}_similarity'.format(strategy)
    generator = globals().get(method_name)
    return generator(gold_mentions, system_mentions)

def get_strict_similarity(gold_mentions, system_mentions):
    num_common_mentions = 0;
    for mention in gold_mentions:
        if mention in system_mentions:
            common_type_exists = 0
            for mention_type in gold_mentions[mention]:
                if mention_type in system_mentions[mention]:
                    common_type_exists = 1
            if common_type_exists:
                num_common_mentions += 1
    return num_common_mentions

def munkres_alignment(matrix):
    cost_matrix = []
    for gold_cluster_number in sorted(matrix):
        cost_row = []
        for system_cluster_number in sorted(matrix[gold_cluster_number]):
            similarity = matrix[gold_cluster_number][system_cluster_number]
            cost_row += [sys.maxsize - similarity]
        cost_matrix += [cost_row]
    return Munkres().compute(cost_matrix)

def align_clusters(args):
    logger = Logger(args.log, args.log_specifications_filename, sys.argv)
    file_types = {
        'gold': args.gold_filename,
        'system': args.system_filename
        }
    clusters = {}
    for file_type, filename in file_types.items():
        for entry in FileHandler(logger, filename):
            metatype = entry.get('?metatype')
            if metatype == 'Relation':
                continue
            cluster_id = entry.get('?cluster')
            mention_span = entry.get('?mention_span')
            mention_type = entry.get('?type')
            t_cv = 1 if file_type == 'gold' else parse_cv(entry.get('?t_cv'))
            cm_cv = 1 if file_type == 'gold' else parse_cv(entry.get('?cm_cv'))
            j_cv = 1 if file_type == 'gold' else parse_cv(entry.get('?j_cv'))
            
            if file_type not in clusters:
                clusters[file_type] = {}
            if cluster_id not in clusters[file_type]:
                clusters[file_type][cluster_id] = {}
            if mention_span not in clusters[file_type][cluster_id]:
                clusters[file_type][cluster_id][mention_span] = {}
            clusters[file_type][cluster_id][mention_span][mention_type] = t_cv * cm_cv * j_cv

    cluster_id_to_number_mapping = {}
    cluster_number_to_id_mapping = {}
    for file_type in clusters:
        number = 0
        cluster_id_to_number_mapping[file_type] = {}
        cluster_number_to_id_mapping[file_type] = {}
        for cluster_id in clusters[file_type]:
            cluster_id_to_number_mapping[file_type][cluster_id] = number
            cluster_number_to_id_mapping[file_type][number] = cluster_id
            number = number + 1

    # similarities is a list of list
    # (x,y) = (gold, system)
    similarity = {}
    for gold_cluster_id in clusters['gold']:
        gold_cluster_number = cluster_id_to_number_mapping['gold'][gold_cluster_id]
        similarity[gold_cluster_number] = {}
        for system_cluster_id in clusters['system']:
            system_cluster_number = cluster_id_to_number_mapping['system'][system_cluster_id]
            similarity[gold_cluster_number][system_cluster_number] = get_similarity(clusters['gold'][gold_cluster_id], clusters['system'][system_cluster_id], strategy='strict')

    max_alignment = munkres_alignment(similarity)
    max_similarity = 0
    for gold_cluster_number, system_cluster_number in max_alignment:
        gold_cluster_id = cluster_number_to_id_mapping['gold'][gold_cluster_number]
        system_cluster_id = cluster_number_to_id_mapping['system'][system_cluster_number]
        value = similarity[gold_cluster_number][system_cluster_number]
        max_similarity += value
        print(f'({gold_cluster_id}, {system_cluster_id}) -> {value}')
    print(f'total profit={max_similarity}')
    
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Align system and gold clusters")
    parser.add_argument('-l', '--log', default='log.txt', 
                        help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, 
                        help='Print version number and exit')
    parser.add_argument('log_specifications_filename', type=str,
                        help='File containing error specifications')
    parser.add_argument('gold_filename', type=str,
                        help='File containing gold clusters, corresponding mentions and types information.')
    parser.add_argument('system_filename', type=str,
                        help='File containing system clusters, corresponding mentions and types information.')
    args = parser.parse_args()
    check_for_paths_existance(args)
    align_clusters(args)