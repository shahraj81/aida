"""
Script for analyzing TA3 scorer log output file for correctness
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "16 May 2022"

from aida.file_handler import FileHandler
from aida.logger import Logger

import argparse
import os
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_for_paths_existance(args):
    for path in [args.log_specifications, args.score, args.score_log]:
        if not os.path.exists(path):
            print('Error: Path {} does not exist'.format(path))
            exit(ERROR_EXIT_CODE)
    for path in [args.output]:
        if os.path.exists(path):
            print('Error: Path {} already exists'.format(path))
            exit(ERROR_EXIT_CODE)

def get_missing_value():
    return ['None', 'N/A']

def get_new_at_ranks(claim_id, values, the_rank, key, value, claim_field_correctness):
    skip = get_missing_value()
    new_compared_to_value_at_ranks = set()
    if key not in ['claim_id']:
        for rank in sorted(values):
            if rank == the_rank: break
            values_at_rank = values.get(rank)
            if key in values_at_rank:
                if values_at_rank.get(key) != value and value not in skip:
                    key_value_pair = '{}:{}'.format(key, value)
                    if claim_field_correctness.get(claim_id).get(key_value_pair):
                        new_compared_to_value_at_ranks.add(str(rank))
        values.setdefault(int(the_rank), {})[key] = value
    return sorted(list(new_compared_to_value_at_ranks))

def is_new_old(values, key, value):
    if key in ['claim_id']: return ''
    # if value in ['None']: return ''
    retVal = '<- new'
    if key in values:
        if value in values.get(key):
            retVal = ''
    values.setdefault(key, set()).add(value)
    return retVal

def parse(line):
    for entry_type in parsers:
        if entry_type in line:
            _, _, _, entry_type, entry_str = line.strip().split(' - ')
            entry = None
            if entry_type in parsers:
                entry = parsers.get(entry_type)(line, entry_type, entry_str)
            return entry

def parse_CLAIM_FIELD_CORRECTNESS(line, entry_type, entry_str):
    return parse_DEFAULT(line, entry_type, entry_str, split_by_1='::', split_by_2=':')

def parse_CLAIM_STRING(line, entry_type, entry_str):
    return parse_DEFAULT(line, entry_type, entry_str, split_by_1='::', split_by_2=':')

def parse_DEFAULT(line, entry_type, entry_str, split_by_1=None, split_by_2=':'):
    key_value_pairs = entry_str.split(split_by_1)
    entry = {'ENTRY_TYPE': entry_type,
             'ENTRY_STR': entry_str,
             'LINE': line.strip()}
    for key_value_pair in key_value_pairs:
        key, value = key_value_pair.split(split_by_2)
        entry[key] = value
    return entry

parsers = {
    'CLAIM_FIELD_CORRECTNESS': parse_CLAIM_FIELD_CORRECTNESS,
    'CLAIM_STRING': parse_CLAIM_STRING,
    'GAIN_VALUE': parse_DEFAULT,
    }

skip = ['ENTRY_STR', 'ENTRY_TYPE', 'LINE']

dependents = {
    'claimEpistemic': ['claimTemplate', 'xVariable'],
    'claimLocation': ['claimEpistemic', 'claimTemplate', 'xVariable', 'claimer'],
    'claimMedium': ['claimEpistemic', 'claimTemplate', 'xVariable', 'claimer'],
    'claimSentiment': ['claimEpistemic', 'claimTemplate', 'xVariable', 'claimer'],
    'claimTemplate': ['claimEpistemic', 'xVariable'],
    'claim_id': [],
    'claimer': ['claimEpistemic', 'claimTemplate', 'xVariable'],
    'claimerAffiliation': ['claimEpistemic', 'claimTemplate', 'xVariable', 'claimer'],
    'date': ['claimEpistemic', 'claimTemplate', 'xVariable', 'claimer'],
    'xVariable': ['claimEpistemic', 'claimTemplate'],
    }

weights = {
    'claimEpistemic': '32',
    'claimLocation': '1',
    'claimMedium': '1',
    'claimSentiment': '0.5',
    'claimTemplate': '32',
    'claim_id': '0',
    'claimer': '16',
    'claimerAffiliation': '4',
    'date': '1',
    'xVariable': '32',
    }

def calculate_gain(fields, value_not_provided_for_fields, incorrect_values):
    fields_counted_as_new = set()
    for fieldname in dependents:
        if fieldname in value_not_provided_for_fields: continue
        if fieldname in incorrect_values: continue
        if fieldname in fields: fields_counted_as_new.add(fieldname)
        else:
            for dependent_fieldname in dependents.get(fieldname):
                if dependent_fieldname in fields:
                    fields_counted_as_new.add(fieldname)
                    break
    gain = 0.0
    for fieldname in fields_counted_as_new:
        # print(fieldname, weights.get(fieldname))
        gain += float(weights.get(fieldname))
    return fields_counted_as_new, gain

def analyze_part_of_logfile(logger, input_filename, condition, claim_relation, ranking_type, query_id, program_output):
    def matches(entry, **kwargs):
        for key, value in kwargs.items():
            if entry.get(key) != value:
                return False
        return True
    claim_field_correctness = {}
    claims = {}
    ranking = []
    if condition == 'Condition5':
        ranking.append({'RANK': '-1', 'GAIN':'N/A', 'POOL_CLAIM_ID':query_id})
    with open(input_filename) as fh:
        for line in fh.readlines():
            entry = parse(line)
            if entry:
                if matches(entry,
                           CLAIM_RELATION=claim_relation,
                           ENTRY_TYPE='GAIN_VALUE',
                           QUERY_ID=query_id,
                           RANKING_TYPE=ranking_type):
                    ranking.append(entry)
                elif matches(entry,
                             ENTRY_TYPE='CLAIM_FIELD_CORRECTNESS'):
                    field_name_and_value = '{}:{}'.format(entry.get('FIELD_NAME'), entry.get('FIELD_VALUE'))
                    claim_field_correctness.setdefault(entry.get('CLAIM_ID'), {})[field_name_and_value] = entry.get('CORRECTNESS')
                elif matches(entry,
                             ENTRY_TYPE='CLAIM_STRING'):
                    claims[entry.get('claim_id')] = entry

    values = {}
    ranks = list()
    for entry in sorted(ranking, key=lambda e: int(e.get('RANK'))):
        fields_new_at_rank = {}
        program_output.write('\n\n--\n')
        rank = entry.get('RANK')
        gain = entry.get('GAIN')
        claim_id = entry.get('POOL_CLAIM_ID')
        claim_entry = claims.get(claim_id)
        program_output.write('rank: {}\n'.format(rank))
        program_output.write('gain: {}\n'.format(gain))
        values_not_provided = set()
        incorrect_values = set()
        for key in sorted(claim_entry.keys()):
            if key in skip: continue
            value = claim_entry.get(key)
            claim_field_correctness_value = claim_field_correctness.get(claim_id).get('{}:{}'.format(key, value))
            correct_or_incorrect = ''
            if value in get_missing_value():
                values_not_provided.add(key)
            elif claim_field_correctness_value == 'False':
                correct_or_incorrect = '*'
                incorrect_values.add(key)
            new_at_ranks = get_new_at_ranks(entry.get('POOL_CLAIM_ID'), values, rank, key, value, claim_field_correctness)
            if correct_or_incorrect == '*':
                new_at_ranks = []
            new_at_ranks_str = 'new compared ranks: {}'.format(new_at_ranks) if len(new_at_ranks) else ''
            for previous_rank in ranks:
                if previous_rank not in fields_new_at_rank:
                    fields_new_at_rank[previous_rank] = set()
                if previous_rank in new_at_ranks:
                    fields_new_at_rank[previous_rank].add(key)
            weight = ' ({})'.format(weights.get(key))
            key_value = '{}{}: {}'.format(key, weight, value)
            spaces = ' '
            num_spaces = 80 - len(key_value)
            if num_spaces > 0 and new_at_ranks_str != '':
                spaces = '.' * num_spaces
            program_output.write('{} {} {}\n'.format(key_value, spaces, new_at_ranks_str))
            program_output.write('    {}{}\n'.format(dependents.get(key), correct_or_incorrect))
        ranks.append(rank)
        program_output.write('\nnew at rank:\n')
        for rank in fields_new_at_rank:
            new_fields = 'None (duplicate)' if len(fields_new_at_rank.get(rank))==0 else ','.join(sorted(fields_new_at_rank.get(rank)))
            fields_counted_as_new, gain = calculate_gain(new_fields, values_not_provided, incorrect_values)
            program_output.write(' {}: {} ({})\n'.format(rank, sorted(fields_counted_as_new), gain))


def analyze_logfile(args):
    logger = Logger(args.log, args.log_specifications, sys.argv)
    input_score_filename = args.score
    input_score_logfilename = args.score_log
    output_directory = args.output
    os.mkdir(output_directory)
    for entry in FileHandler(None, input_score_filename):
        condition = entry.get('Condition')
        query_id = entry.get('QueryID')
        claim_relation = entry.get('ClaimRelation')
        if query_id != 'ALL-Macro':
            for ranking_type in ['submitted', 'ideal']:
                output_filename = os.path.join(output_directory, 'ranking_{}_{}_{}.txt'.format(query_id, claim_relation, ranking_type))
                with open(output_filename, 'w') as program_output:
                    analyze_part_of_logfile(logger, input_score_logfilename, condition, claim_relation, ranking_type, query_id, program_output)
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyze TA3 scorer log output file")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('score', type=str, help='Input score tab file')
    parser.add_argument('score_log', type=str, help='Input score log file')
    parser.add_argument('output', type=str, help='Output directory')
    args = parser.parse_args()
    check_for_paths_existance(args)
    analyze_logfile(args)