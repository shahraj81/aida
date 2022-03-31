"""
Script for AIDA evaluation pipeline for Task3.

This script performs the following steps:

    1. Apply SPARQL queries to the KB,
    2. Clean SPARQL output,
    3. Validate SPARQL output,

This version of the docker works for M54 (i.e. Phase 3).
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "2020.1.0"
__date__    = "16 February 2022"

from logger import Logger
from object import Object
import argparse
import os
import re
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def call_system(cmd):
    cmd = ' '.join(cmd.split())
    print("running system command: '{}'".format(cmd))
    os.system(cmd)

def get_problems(logs_directory):
    num_errors = 0
    stats = {}
    for filename in os.listdir(logs_directory):
        filepath = '{}/{}'.format(logs_directory, filename)
        fh = open(filepath)
        for line in fh.readlines():
            if 'ERROR' in line:
                num_errors += 1
                error_type = line.split('-')[3].strip()
                stats[error_type] = stats.get(error_type, 0) + 1
        fh.close()
    return num_errors, stats

def record_and_display_message(logger, message):
    print("-------------------------------------------------------------------------------")
    print(message)
    print("-------------------------------------------------------------------------------")
    logger.record_event('DEFAULT_INFO', message)

def trim(s):
    return s.replace('.ttl', '') if s is not None and s.endswith('.ttl') else s

class ClaimRankings(Object):
    def __init__(self, logger, input_path, arg_depth):
        super().__init__(logger)
        self.depth = {}
        if arg_depth:
            for condition_and_depth in arg_depth.split(','):
                c, d = condition_and_depth.split(':')
                self.depth[c] = int(d)
        self.input_path = input_path
        self.ranks = {}

    def generate_pool(self):
        def generate(query_claims, depth):
            for query_id in query_claims:
                bins = {}
                for claim_id, claim_relation_and_rank in query_claims.get(query_id).items():
                    claim_relation = claim_relation_and_rank.get('claim_relation')
                    rank = claim_relation_and_rank.get('rank')
                    if claim_relation not in bins:
                        bins[claim_relation] = {}
                    bins.get(claim_relation)[rank] = claim_id
                for claim_relation in bins:
                    claim_relation_bin = bins.get(claim_relation)
                    i = 0
                    for rank in sorted(claim_relation_bin.keys()):
                        i += 1
                        claim_id = claim_relation_bin.get(rank)
                        pooled = True if depth is None or i <= depth else False
                        query_claims.get(query_id).get(claim_id)['pooled'] = pooled
        ranks = self.get('ranks')
        for condition in ranks:
            query_claims = ranks.get(condition)
            generate(query_claims, self.get('depth').get(condition) if self.get('depth') else None)

    def get_claim(self, claim_condition, query_id, claim_id):
        return self.get('ranks').get(claim_condition).get(query_id).get(claim_id)

    def include_in_pool(self, filename):
        p = self.parse(filename)
        claim = self.get('claim', p.get('claim_condition'), p.get('query_id'), p.get('claim_id'))
        return claim.get('pooled')

    def load_file(self, filename):
        claim_condition = self.parse(filename).get('claim_condition')
        with open(filename) as fh:
            for line in fh.readlines():
                elements = line.strip().split('\t')
                query_id, claim_id, rank = [elements[i] for i in range(3)]
                claim_relation = 'related' if len(elements) == 3 else elements[3]
                self.get('ranks').setdefault(claim_condition, {}) \
                     .setdefault(query_id, {})[claim_id] = {
                         'claim_relation': claim_relation,
                         'filename': filename,
                         'line': line,
                         'rank': int(rank)
                         }
        return

    def parse(self, filename):
        filename = filename.replace(self.get('input_path'), '')
        if filename.startswith('/'):
            filename = filename.replace('/', '', 1)
        claim_condition, query_id, claim_id = filename.split('/')
        claim_id = None if claim_id.endswith('.ranking.tsv') else claim_id
        return {
            'claim_condition': claim_condition,
            'query_id': query_id,
            'claim_id': trim(claim_id)
            }

    def write_to_files(self, output_dir):
        lines = {}
        ranks = self.get('ranks')
        for condition in ranks:
            queries = ranks.get(condition)
            for query_id in queries:
                for claim in queries.get(query_id).values():
                    if claim.get('pooled'):
                        input_ranking_filename = claim.get('filename')
                        output_ranking_filename = input_ranking_filename.replace(self.get('input_path'), output_dir)
                        line = claim.get('line')
                        lines.setdefault(output_ranking_filename, []).append(line)
        for output_ranking_filename in lines:
            with open(output_ranking_filename, 'w') as program_output:
                for line in lines.get(output_ranking_filename):
                    program_output.write(line)

def main(args):

    #############################################################################################
    # check input/output directory for existence
    #############################################################################################

    print("Checking if input/output directories exist.")
    for path in [args.input, args.output]:
        if not os.path.exists(path):
            print('ERROR: Path {} does not exist'.format(path))
            exit(ERROR_EXIT_CODE)
    print("Checking if output directory is empty.")
    files = [f for f in os.listdir(args.output)]
    if len(files) > 0:
        print('ERROR: Output directory {} is not empty'.format(args.output))
        exit(ERROR_EXIT_CODE)

    #############################################################################################
    # create logger
    #############################################################################################

    logs_directory = '{output}/{logs}'.format(output=args.output, logs=args.logs)
    run_log_file = '{logs_directory}/run.log'.format(logs_directory=logs_directory)
    call_system('mkdir {logs_directory}'.format(logs_directory=logs_directory))
    logger = Logger(run_log_file, args.spec, sys.argv)

    #############################################################################################
    # validate values of arguments
    #############################################################################################

    p = re.compile('^Condition5:\d+,Condition6:\d+,Condition7:\d+$')
    if not(args.depth is None or (args.depth and p.match(args.depth))):
        record_and_display_message(logger, 'Invalid depth: {}.'.format(args.depth))
        exit(ERROR_EXIT_CODE)

    runtypes = {
        'develop': 'develop',
        'practice': 'LDC2021E11',
        'evaluation': 'LDC2022R02'}
    if args.runtype not in runtypes:
        logger.record_event('UNKNOWN_RUNTYPE', args.runtype, ','.join(runtypes))
        exit(ERROR_EXIT_CODE)

    ldc_package_id = runtypes[args.runtype]
    record_and_display_message(logger, 'Docker is using {} data.'.format(args.runtype))

    #############################################################################################
    # AUX-data
    #############################################################################################

    python_scripts          = '/scripts/aida/python'
    log_specifications      = '{}/input/aux_data/log_specifications.txt'.format(python_scripts)
    encoding_modality       = '/data/AUX-data/encoding_modality.txt'
    coredocs                = '/data/AUX-data/{}.coredocs.txt'.format(ldc_package_id)
    parent_children         = '/data/AUX-data/{}.parent_children.tsv'.format(ldc_package_id)
    sentence_boundaries     = '/data/AUX-data/{}.sentence_boundaries.txt'.format(ldc_package_id)
    image_boundaries        = '/data/AUX-data/{}.image_boundaries.txt'.format(ldc_package_id)
    keyframe_boundaries     = '/data/AUX-data/{}.keyframe_boundaries.txt'.format(ldc_package_id)
    video_boundaries        = '/data/AUX-data/{}.video_boundaries.txt'.format(ldc_package_id)
    ltf_directory           = '/data/ltf'
    sparql_kb_source        = '{output}/SPARQL-KB-source'.format(output=args.output)
    sparql_kb_input         = '{output}/SPARQL-KB-input'.format(output=args.output)
    sparql_output           = '{output}/SPARQL-output'.format(output=args.output)
    sparql_clean_output     = '{output}/SPARQL-CLEAN-output'.format(output=args.output)
    sparql_merged_output    = '{output}/SPARQL-MERGED-output'.format(output=args.output)
    sparql_valid_output     = '{output}/SPARQL-VALID-output'.format(output=args.output)
    sparql_augmented_output = '{output}/SPARQL-AUGMENTED-output'.format(output=args.output)
    arf_output              = '{output}/ARF-output'.format(output=args.output)

    #############################################################################################
    # pull latest copy of code from git
    #############################################################################################

    call_system('cd {python_scripts} && git pull'.format(python_scripts=python_scripts))

    #############################################################################################
    # inspect the input directory
    #############################################################################################

    record_and_display_message(logger, 'Inspecting the input directory.')

    for destination in [sparql_kb_source, sparql_kb_input]:
        call_system('mkdir {destination}'.format(destination=destination))
    items = [f for f in os.listdir(args.input)]

    num_items = len(items)
    s3_location_provided = False
    if num_items == 1:
        filename = items[0]
        if filename == 's3_location.txt':
            s3_location_provided = True
    num_files = 0
    input_filenames_including_path = {}
    if s3_location_provided:
        if args.aws_access_key_id is None or args.aws_secret_access_key is None:
            logger.record_event('MISSING_AWS_CREDENTIALS')
            exit(ERROR_EXIT_CODE)
        call_system('mkdir /root/.aws')
        with open('/root/.aws/credentials', 'w') as credentials:
            credentials.write('[default]\n')
            credentials.write('aws_access_key_id = {}\n'.format(args.aws_access_key_id))
            credentials.write('aws_secret_access_key = {}\n'.format(args.aws_secret_access_key))
        call_system('cp {path}/{filename} {destination}/source.txt'.format(path=args.input, filename=filename, destination=sparql_kb_source))
        with open('{path}/{filename}'.format(path=args.input, filename=filename)) as fh:
            lines = fh.readlines()
            if len(lines) != 1:
                logger.record_event('UNEXPECTED_NUM_LINES_IN_INPUT', 1, len(lines))
                exit(ERROR_EXIT_CODE)
            s3_location = lines[0].strip()
            if not s3_location.startswith('s3://aida-') and not s3_location.endswith('.tgz'):
                logger.record_event('UNEXPECTED_S3_LOCATION', 's3://aida-*/*.tgz', s3_location)
                exit(ERROR_EXIT_CODE)
            s3_filename = s3_location.split('/')[-1]
            call_system('mkdir /tmp/s3_run/')
            record_and_display_message(logger, 'Downloading {s3_location}.'.format(s3_location=s3_location))
            call_system('aws s3 cp {s3_location} /tmp/s3_run/'.format(s3_location=s3_location))
            uncompress_command = None
            if s3_filename.endswith('.zip'):
                uncompress_command = 'unzip'
            if s3_filename.endswith('.tgz'):
                uncompress_command = 'tar -zxf'
            call_system('cd /tmp/s3_run && {uncompress_command} {s3_filename}'.format(s3_filename=s3_filename,
                                                                                      uncompress_command=uncompress_command))
            call_system('mv /tmp/s3_run/output/*/NIST /tmp/s3_run/NIST')

    input_path = '/tmp/s3_run/NIST' if s3_location_provided else args.input
    claim_rankings = ClaimRankings(logger, input_path, args.depth)
    for dirpath, dirnames, filenames in os.walk(input_path):
        for filename in filenames:
            filename_including_path = os.path.join(dirpath, filename)
            if filename.endswith('-report.txt'):
                filename_including_path = '{}.ttl'.format(filename_including_path.replace('-report.txt', ''))
                input_filenames_including_path[filename_including_path] = 0
            elif filename.endswith('.ttl'):
                if filename_including_path not in input_filenames_including_path:
                    input_filenames_including_path[filename_including_path] = 1
            elif filename.endswith('.ranking.tsv'):
                claim_rankings.load_file(filename_including_path)
    claim_rankings.generate_pool()
    for filename_including_path in input_filenames_including_path:
        if input_filenames_including_path[filename_including_path] == 0:
            record_and_display_message(logger, 'Ignoring invalid KB: {}'.format(filename_including_path.replace(input_path, '')))
        elif input_filenames_including_path[filename_including_path] == 1:
            if claim_rankings.include_in_pool(filename_including_path):
                record_and_display_message(logger, 'Copying {}'.format(filename_including_path.replace(input_path, '')))
                destination = filename_including_path.replace(input_path, sparql_kb_input)
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                call_system('cp {filename_including_path} {destination}'.format(filename_including_path=filename_including_path,
                                                                                 destination=destination))
                num_files += 1
            else:
                record_and_display_message(logger, 'Skipping {}'.format(filename_including_path.replace(input_path, '')))
    claim_rankings.write_to_files(sparql_kb_input)
    if s3_location_provided:
        call_system('rm -rf /tmp/s3_run/')

    #############################################################################################
    # verify the input directory structure
    #############################################################################################

    record_and_display_message(logger, 'Verifying input directory structure.')

    log_file = '{logs_directory}/verify-output-directory-structure.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3.9 verify_output_directory_structure.py \
            task3 \
            --log {log_file} \
            {log_specifications} \
            {queries} \
            {sparql_kb_input}'.format(python_scripts=python_scripts,
                                      log_file=log_file,
                                      log_specifications=log_specifications,
                                      queries='/data/user-queries',
                                      sparql_kb_input=sparql_kb_input)
    call_system(cmd)

    num_errors, _ = get_problems(logs_directory)
    if num_errors:
        logger.record_event('IMPROPER_INPUT_DIRECTORY_STRUCTURE', sparql_kb_input)
        exit(ERROR_EXIT_CODE)

    #############################################################################################
    # process each condition and topic_or_claim_frame independently
    #############################################################################################

    # copy TA3 SPARQL queries
    queries = '{}/queries'.format(args.output)
    record_and_display_message(logger, 'Copying SPARQL queries to be applied.')
    call_system('mkdir {queries}'.format(queries=queries))
    call_system('cp /data/queries/AIDA_P3_TA3_*.rq {queries}'.format(task=args.task, queries=queries))

    c_cnt = 0
    created = set()
    condition_directories = os.listdir(sparql_kb_input)
    for condition_name in condition_directories:
        c_cnt += 1
        condition_directory = os.path.join(sparql_kb_input, condition_name)
        topic_or_claim_frame_directories = os.listdir(condition_directory)
        t_cnt = 0
        for topic_or_claim_frame_id in topic_or_claim_frame_directories:
            t_cnt += 1
            topic_or_claim_frame_directory = os.path.join(condition_directory, topic_or_claim_frame_id)
            output_conditions_directory = '{output}/SPARQL-output/{condition_name}'.format(output=args.output,
                                                                                           condition_name=condition_name)
            if output_conditions_directory not in created:
                record_and_display_message(logger, 'Creating directory: {}'.format(output_conditions_directory))
                os.makedirs(output_conditions_directory)
                created.add(output_conditions_directory)

            sparql_output_subdir = '{output_conditions_directory}/{topic_or_claim_frame_id}'.format(output_conditions_directory=output_conditions_directory,
                                                                                                    topic_or_claim_frame_id=topic_or_claim_frame_id)
            record_and_display_message(logger, 'Creating output directory: {}'.format(sparql_output_subdir))
            os.makedirs(sparql_output_subdir)
            # copy ranking file
            input_ranking_file = '{output}/SPARQL-KB-input/{condition_name}/{topic_or_claim_frame_id}/{topic_or_claim_frame_id}.ranking.tsv'
            input_ranking_file = input_ranking_file.format(output=args.output,
                                                           condition_name=condition_name,
                                                           topic_or_claim_frame_id=topic_or_claim_frame_id)
            call_system('cp {input_ranking_file} {sparql_output_subdir}'.format(input_ranking_file=input_ranking_file,
                                                                                sparql_output_subdir=sparql_output_subdir))
            #############################################################################################
            # apply sparql queries
            ############################################################################################
            graphdb_bin = '/opt/graphdb/dist/bin'
            graphdb = '{}/graphdb'.format(graphdb_bin)
            loadrdf = '{}/loadrdf'.format(graphdb_bin)
            verdi = '/opt/sparql-evaluation'
            jar = '{}/sparql-evaluation-1.0.0-SNAPSHOT-all.jar'.format(verdi)
            config = '{}/config/Local-config.ttl'.format(verdi)
            properties = '{}/config/Local-config.properties'.format(verdi)
            intermediate = '{}/intermediate'.format(sparql_output_subdir)

            k_cnt = 0
            kb_filenames = [f for f in os.listdir(topic_or_claim_frame_directory) if os.path.isfile(os.path.join(topic_or_claim_frame_directory, f)) and f.endswith('.ttl')]
            for kb_filename in kb_filenames:
                kb_filename_including_path = os.path.join(topic_or_claim_frame_directory, kb_filename)
                k_cnt += 1
                record_and_display_message(logger, 'Applying queries to {condition} ({c_cnt}/{c_tot}) {topic} ({t_cnt}/{t_tot}) {kb_filename} ({k_cnt}/{k_tot}).'.format(condition=condition_name,
                                                                                                                                                                           c_cnt=c_cnt,
                                                                                                                                                                           c_tot=len(condition_directories),
                                                                                                                                                                           topic=topic_or_claim_frame_id,
                                                                                                                                                                           t_cnt=t_cnt,
                                                                                                                                                                           t_tot=len(topic_or_claim_frame_directories),
                                                                                                                                                                           kb_filename=kb_filename,
                                                                                                                                                                           k_cnt=k_cnt,
                                                                                                                                                                           k_tot=len(kb_filenames)))
                # create the intermediate directory
                logger.record_event('DEFAULT_INFO', 'Creating {}.'.format(intermediate))
                call_system('mkdir -p {}'.format(intermediate))
                # load KB into GraphDB
                logger.record_event('DEFAULT_INFO', 'Loading {kb_filename} into GraphDB.'.format(kb_filename=kb_filename))
                input_kb = '{kb_filename_including_path}'.format(kb_filename_including_path=kb_filename_including_path)
                call_system('{loadrdf} -c {config} -f -m parallel {input}'.format(loadrdf=loadrdf, config=config, input=input_kb))
                # start GraphDB
                logger.record_event('DEFAULT_INFO', 'Starting GraphDB')
                call_system('{graphdb} -d'.format(graphdb=graphdb))
                # wait for GraphDB
                call_system('sleep 5')
                # apply queries
                logger.record_event('DEFAULT_INFO', 'Applying queries')
                call_system('java -Xmx4096M -jar {jar} -c {properties} -q {queries} -o {intermediate}/'.format(jar=jar,
                                                                                          properties=properties,
                                                                                          queries=queries,
                                                                                          intermediate=intermediate))
                # generate the SPARQL output directory corresponding to the KB
                logger.record_event('DEFAULT_INFO', 'Creating SPARQL output directory corresponding to the KB')
                call_system('mkdir {output}/{kb_filename}'.format(output=sparql_output_subdir, kb_filename=kb_filename))
                # move output out of intermediate into the output corresponding to the KB
                logger.record_event('DEFAULT_INFO', 'Moving output out of the intermediate directory')
                call_system('mv {intermediate}/*/* {output}/{kb_filename}'.format(intermediate=intermediate,
                                                                                  kb_filename=kb_filename,
                                                                                  output=sparql_output_subdir))
                # remove intermediate directory
                logger.record_event('DEFAULT_INFO', 'Removing the intermediate directory.')
                call_system('rm -rf {}'.format(intermediate))
                # stop GraphDB
                logger.record_event('DEFAULT_INFO', 'Stopping GraphDB.')
                call_system('pkill -9 -f graphdb')

            message = 'SPARQL output generated.'
            record_and_display_message(logger, '{}'.format(message))

    #############################################################################################
    # Clean SPARQL output
    #############################################################################################

    record_and_display_message(logger, 'Cleaning SPARQL output.')
    log_file = '{logs_directory}/clean-sparql-output.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3.9 clean_sparql_output.py \
            --log {log_file} \
            {log_specifications} \
            {sparql_output} \
            {sparql_clean_output}'.format(python_scripts=python_scripts,
                                          log_file=log_file,
                                          log_specifications=log_specifications,
                                          sparql_output=sparql_output,
                                          sparql_clean_output=sparql_clean_output)
    call_system(cmd)

    #############################################################################################
    # Merge SPARQL output
    #############################################################################################

    record_and_display_message(logger, 'Merging SPARQL output.')

    log_file = '{logs_directory}/merge-output.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3.9 augment_output.py \
            merge \
            --log {log_file} \
            --task task3 \
            {log_specifications} \
            {sparql_clean_output} \
            {sparql_merged_output}'.format(python_scripts=python_scripts,
                                           log_file=log_file,
                                           log_specifications=log_specifications,
                                           sparql_clean_output = sparql_clean_output,
                                           sparql_merged_output = sparql_merged_output)
    call_system(cmd)

    #############################################################################################
    # Validate SPARQL output
    #############################################################################################

    record_and_display_message(logger, 'Validating SPARQL output.')

    log_file = '{logs_directory}/validate-responses.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3.9 validate_responses.py \
            --log {log_file} \
            --queries {queries} \
            --task task3 \
            {log_specifications} \
            {encoding_modality} \
            {coredocs} \
            {parent_children} \
            {sentence_boundaries} \
            {image_boundaries} \
            {keyframe_boundaries} \
            {video_boundaries} \
            {run_id} \
            {sparql_merged_output} \
            {sparql_valid_output}'.format(python_scripts=python_scripts,
                                           log_file=log_file,
                                           queries='/data/user-queries',
                                           log_specifications=log_specifications,
                                           encoding_modality=encoding_modality,
                                           coredocs=coredocs,
                                           parent_children=parent_children,
                                           sentence_boundaries=sentence_boundaries,
                                           image_boundaries=image_boundaries,
                                           keyframe_boundaries=keyframe_boundaries,
                                           video_boundaries=video_boundaries,
                                           run_id=args.run,
                                           sparql_merged_output=sparql_merged_output,
                                           sparql_valid_output=sparql_valid_output)
    call_system(cmd)

    #############################################################################################
    # Replacing missing handle-span with text, if provided
    #############################################################################################

    record_and_display_message(logger, 'Replacing missing handle-span with text, if provided.')

    if os.path.exists(ltf_directory):
        log_file = '{logs_directory}/augment-handle-output.log'.format(logs_directory=logs_directory)
        cmd = 'cd {python_scripts} && \
                python3.9 augment_output.py \
                handle \
                --log {log_file} \
                --task task3 \
                {log_specifications} \
                {ltf_directory} \
                {sparql_valid_output} \
                {sparql_augmented_output}'.format(python_scripts=python_scripts,
                                                  log_file=log_file,
                                                  log_specifications=log_specifications,
                                                  ltf_directory=ltf_directory,
                                                  sparql_valid_output = sparql_valid_output,
                                                  sparql_augmented_output = sparql_augmented_output)
    else:
        record_and_display_message(logger, '{ltf_directory} does not exist, skipping replacing missing handle-span with text.'.format(ltf_directory=ltf_directory))
        cmd = 'cp -r {source} {destination}'.format(source=sparql_valid_output, destination=sparql_augmented_output)

    call_system(cmd)

    #############################################################################################
    # Generate ARF output
    #############################################################################################

    record_and_display_message(logger, 'Generating ARF output.')

    log_file = '{logs_directory}/generate-arf.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3.9 generate_arf.py \
            --log {log_file} \
            --queries {queries} \
            {log_specifications} \
            {encoding_modality} \
            {coredocs} \
            {parent_children} \
            {sentence_boundaries} \
            {image_boundaries} \
            {keyframe_boundaries} \
            {video_boundaries} \
            {run_id} \
            {sparql_augmented_output} \
            {arf_output}'.format(python_scripts=python_scripts,
                                           log_file=log_file,
                                           queries='/data/user-queries',
                                           log_specifications=log_specifications,
                                           encoding_modality=encoding_modality,
                                           coredocs=coredocs,
                                           parent_children=parent_children,
                                           sentence_boundaries=sentence_boundaries,
                                           image_boundaries=image_boundaries,
                                           keyframe_boundaries=keyframe_boundaries,
                                           video_boundaries=video_boundaries,
                                           run_id=args.run,
                                           sparql_augmented_output=sparql_augmented_output,
                                           arf_output=arf_output)
    call_system(cmd)

    record_and_display_message(logger, 'Done.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Apply AIDA M36 task2 evaluation pipeline to the KB.")
    parser.add_argument('-d', '--depth', help='Specify the pool depth')
    parser.add_argument('-i', '--input', default='/evaluate', help='Specify the input directory (default: %(default)s)')
    parser.add_argument('-I', '--aws_access_key_id', help='aws_access_key_id; required if the KB is to be obtained from an S3 location')
    parser.add_argument('-K', '--aws_secret_access_key', help='aws_secret_access_key; required if the KB is to be obtained from an S3 location')
    parser.add_argument('-l', '--logs', default='logs', help='Specify the name of the logs directory to which different log files should be written (default: %(default)s)')
    parser.add_argument('-o', '--output', default='/output', help='Specify the output directory (default: %(default)s)')
    parser.add_argument('-r', '--run', default='system', help='Specify the run name (default: %(default)s)')
    parser.add_argument('-R', '--runtype', default='practice', help='Specify the run type (default: %(default)s)')
    parser.add_argument('-s', '--spec', default='/scripts/log_specifications.txt', help='Specify the log specifications file (default: %(default)s)')
    parser.add_argument('-t', '--task', default='task3', help='Specify the task in order to apply relevant queries (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__,  help='Print version number and exit')
    args = parser.parse_args()
    main(args)
