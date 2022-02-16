"""
Script for AIDA evaluation pipeline for Task3.

This script performs the following steps:

    1. Apply SPARQL queries to the KB,
    2. Clean SPARQL output,
    3. Validate SPARQL output,

This version of the docker works for M54 (i.e. Phase 3).
"""

# this script needs revision due to changed directory structure

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "2020.1.0"
__date__    = "16 February 2022"

from logger import Logger
import argparse
import os
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
    print("-------------------------------------------------------")
    print(message)
    print("-------------------------------------------------------")
    logger.record_event('DEFAULT_INFO', message)

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
    sparql_kb_source        = '{output}/SPARQL-KB-source'.format(output=args.output)
    sparql_kb_input         = '{output}/SPARQL-KB-input'.format(output=args.output)

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

            for dirpath, dirnames, filenames in os.walk('/tmp/s3_run/'):
                for kb_filename in [f for f in filenames if f.endswith('.ttl')]:
                    if len(dirpath.split('/')) == 6 and os.path.basename(dirpath) == 'NIST':
                        kb_filename_including_path = os.path.join(dirpath, kb_filename)
                        # consider all kbs valid
                        record_and_display_message(logger, 'Copying {}'.format(kb_filename_including_path.replace('/tmp/s3_run/', '')))
                        call_system('cp {kb_filename_including_path} {destination}/'.format(kb_filename_including_path=kb_filename_including_path,
                                                                                            destination=sparql_kb_input))
                        num_files += 1
            call_system('rm -rf /tmp/s3_run')
    else:
        # pull all ttl files in (even if they are not valid)
        logger.record_event('DEFAULT_INFO', 'Copying everything from {input}'.format(input=args.input))
        call_system('cp -r {input}/* {destination}'.format(input=args.input, destination=sparql_kb_input))

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
                                      queries='/data/queries/ta3_query_claim_frames',
                                      sparql_kb_input=sparql_kb_input)
    call_system(cmd)

    num_errors, _ = get_problems(logs_directory)
    if num_errors:
        logger.record_event('IMPROPER_INPUT_DIRECTORY_STRUCTURE', sparql_kb_input)
        record_and_display_message(logger, 'Improper structure of input directory: {}'.format(sparql_kb_input))
        exit(ERROR_EXIT_CODE)

    #############################################################################################
    # process each condition and topic_or_claim_frame independently
    #############################################################################################

    output_locations_init = {
        'sparql_output': 'SPARQL-output',
        'sparql_clean_output': 'SPARQL-CLEAN-output',
        'sparql_merged_output': 'SPARQL-MERGED-output',
        'sparql_valid_output': 'SPARQL-VALID-output',
        'arf_output': 'ARF-output',
        'logs': 'logs'
        }

    # copy TA3 SPARQL queries
    queries = '{}/queries'.format(args.output)
    record_and_display_message(logger, 'Copying SPARQL queries to be applied.')
    call_system('mkdir {queries}'.format(queries=queries))
    call_system('cp /data/queries/AIDA_P3_TA3_*.rq {queries}'.format(task=args.task, queries=queries))

    for condition_name in os.listdir(sparql_kb_input):
        condition_directory = os.path.join(sparql_kb_input, condition_name)
        for topic_or_claim_frame_id in os.listdir(condition_directory):
            topic_or_claim_frame_directory = os.path.join(condition_directory, topic_or_claim_frame_id)
            record_and_display_message(logger, 'Creating output directory: {}'.format(topic_or_claim_frame_directory))
            os.makedirs(topic_or_claim_frame_directory)
            output_locations = {}
            for k,v in output_locations_init.items():
                output_locations[k] = '{topic_or_claim_frame_directory}/{v}'.format(topic_or_claim_frame_directory=topic_or_claim_frame_directory,
                                                                                    v=v)

            #############################################################################################
            # apply sparql queries
            ############################################################################################
            record_and_display_message(logger, 'Applying SPARQL queries to condition:\'{}\' topic_or_claim_frame_id: \'{}\''.format(condition_name,
                                                                                                                                    topic_or_claim_frame_id))
            graphdb_bin = '/opt/graphdb/dist/bin'
            graphdb = '{}/graphdb'.format(graphdb_bin)
            loadrdf = '{}/loadrdf'.format(graphdb_bin)
            verdi = '/opt/sparql-evaluation'
            jar = '{}/sparql-evaluation-1.0.0-SNAPSHOT-all.jar'.format(verdi)
            config = '{}/config/Local-config.ttl'.format(verdi)
            properties = '{}/config/Local-config.properties'.format(verdi)
            sparql_output = output_locations.get('sparql_output')
            sparql_clean_output = output_locations.get('sparql_clean_output')
            sparql_merged_output = output_locations.get('sparql_merged_output')
            sparql_valid_output = output_locations.get('sparql_valid_output')
            arf_output = output_locations.get('arf_output')
            intermediate = '{}/intermediate'.format(sparql_output)

            count = 0
            kb_filenames = [f for f in os.listdir(topic_or_claim_frame_directory) if os.path.isfile(f) and f.endswith('.ttl')]
            for kb_filename in kb_filenames:
                kb_filename_including_path = os.path.join(topic_or_claim_frame_directory, kb_filename)
                count += 1
                record_and_display_message(logger, 'Applying queries to {kb_filename} ... {count} of {num_total}.'.format(count=count,
                                                                                                                          num_total=len(kb_filenames),
                                                                                                                          kb_filename=kb_filename))
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
                call_system('mkdir {output}/{kb_filename}'.format(output=sparql_output, kb_filename=kb_filename))
                # move output out of intermediate into the output corresponding to the KB
                logger.record_event('DEFAULT_INFO', 'Moving output out of the intermediate directory')
                call_system('mv {intermediate}/*/* {output}/{kb_filename}'.format(intermediate=intermediate,
                                                                                  kb_filename=kb_filename,
                                                                                  output=sparql_output))
                # remove intermediate directory
                logger.record_event('DEFAULT_INFO', 'Removing the intermediate directory.')
                call_system('rm -rf {}'.format(intermediate))
                # stop GraphDB
                logger.record_event('DEFAULT_INFO', 'Stopping GraphDB.')
                call_system('pkill -9 -f graphdb')

            message = 'SPARQL output generated.'
            record_and_display_message(logger, '{}\n'.format(message))

            #############################################################################################
            # Clean SPARQL output
            #############################################################################################

            record_and_display_message(logger, 'Cleaning SPARQL output.')
            log_file = '{logs_directory}/clean-sparql-output.log'.format(logs_directory=output_locations.get('logs'))
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

            log_file = '{logs_directory}/merge-output.log'.format(logs_directory=output_locations.get('logs'))
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

            log_file = '{logs_directory}/validate-responses.log'.format(logs_directory=output_locations.get('logs'))
            cmd = 'cd {python_scripts} && \
                    python3.9 validate_responses.py \
                    --log {log_file} \
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
            # Generate ARF output
            #############################################################################################

            record_and_display_message(logger, 'Generating ARF output.')

            log_file = '{logs_directory}/generate-arf.log'.format(logs_directory=output_locations.get('logs'))
            cmd = 'cd {python_scripts} && \
                    python3.9 generate_arf.py \
                    --log {log_file} \
                    {log_specifications} \
                    {encoding_modality} \
                    {coredocs} \
                    {parent_children} \
                    {sentence_boundaries} \
                    {image_boundaries} \
                    {keyframe_boundaries} \
                    {video_boundaries} \
                    {run_id} \
                    {sparql_valid_output} \
                    {arf_output}'.format(python_scripts=python_scripts,
                                                   log_file=log_file,
                                                   log_specifications=log_specifications,
                                                   encoding_modality=encoding_modality,
                                                   coredocs=coredocs,
                                                   parent_children=parent_children,
                                                   sentence_boundaries=sentence_boundaries,
                                                   image_boundaries=image_boundaries,
                                                   keyframe_boundaries=keyframe_boundaries,
                                                   video_boundaries=video_boundaries,
                                                   run_id=args.run,
                                                   sparql_valid_output=sparql_valid_output,
                                                   arf_output=arf_output)
            call_system(cmd)

    record_and_display_message(logger, 'Done.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Apply AIDA M36 task2 evaluation pipeline to the KB.")
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
