"""
Script for AIDA evaluation pipeline for Task2.

This script performs the following steps:

    1. Apply SPARQL queries to the KB,
    2. Clean SPARQL output,
    3. Validate SPARQL output,

This version of the docker works for M36.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "2020.1.0"
__date__    = "6 Oct 2020"

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
        'practice': 'LDC2020E11',
        'evaluation': 'LDC2020R17'}
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
    ontology_type_mappings  = '/data/AUX-data/AIDA_Annotation_Ontology_Phase2_V1.1_typemappings.tab'
    slotname_mappings       = '/data/AUX-data/AIDA_Annotation_Ontology_Phase2_V1.1_slotnamemappings.tab'
    encoding_modality       = '/data/AUX-data/encoding_modality.txt'
    coredocs                = '/data/AUX-data/{}.coredocs.txt'.format(ldc_package_id)
    parent_children         = '/data/AUX-data/{}.parent_children.tsv'.format(ldc_package_id)
    sentence_boundaries     = '/data/AUX-data/{}.sentence_boundaries.txt'.format(ldc_package_id)
    image_boundaries        = '/data/AUX-data/{}.image_boundaries.txt'.format(ldc_package_id)
    keyframe_boundaries     = '/data/AUX-data/{}.keyframe_boundaries.txt'.format(ldc_package_id)
    video_boundaries        = '/data/AUX-data/{}.video_boundaries.txt'.format(ldc_package_id)
    sparql_kb_input         = '{output}/SPARQL-KB-input'.format(output=args.output)
    sparql_output           = '{output}/SPARQL-output'.format(output=args.output)
    sparql_valid_output     = '{output}/SPARQL-VALID-output'.format(output=args.output)

    #############################################################################################
    # pull latest copy of code from git
    #############################################################################################

    call_system('cd {python_scripts} && git pull'.format(python_scripts=python_scripts))

    #############################################################################################
    # inspect the input directory
    #############################################################################################

    record_and_display_message(logger, 'Inspecting the input directory.')
    items = [f for f in os.listdir(args.input)]
    if len(items) != 1:
        logger.record_event('UNEXPECTED_NUM_FILES_IN_INPUT', 1, len(items))
        exit(ERROR_EXIT_CODE)
    else:
        filename = items[0]
        expected_filenames = ['task2_kb.ttl', 's3_location.txt']
        if filename not in expected_filenames:
            logger.record_event('UNEXPECTED_FILENAME', ','.join(expected_filenames), filename)
            exit(ERROR_EXIT_CODE)
        call_system('mkdir {destination}'.format(destination=sparql_kb_input))
        if filename == 's3_location.txt':
            if args.aws_access_key_id is None or args.aws_secret_access_key is None:
                logger.record_event('MISSING_AWS_CREDENTIALS')
                exit(ERROR_EXIT_CODE)
            call_system('mkdir /root/.aws')
            with open('/root/.aws/credentials', 'w') as credentials:
                credentials.write('[default]\n')
                credentials.write('aws_access_key_id = {}\n'.format(args.aws_access_key_id))
                credentials.write('aws_secret_access_key = {}\n'.format(args.aws_secret_access_key))
            with open('{path}/{filename}'.format(path=args.input, filename=filename)) as fh:
                lines = fh.readlines()
                if len(lines) != 1:
                    logger.record_event('UNEXPECTED_NUM_LINES_IN_INPUT', 1, len(lines))
                    exit(ERROR_EXIT_CODE)
                s3_location = lines[0].strip()
                if not s3_location.startswith('s3://aida-phase2-ta-performers/'):
                    logger.record_event('UNEXPECTED_S3_LOCATION', 's3://aida-phase2-ta-performers/...', s3_location)
                    exit(ERROR_EXIT_CODE)
                s3_filename = s3_location.split('/')[-1]
                call_system('mkdir /tmp/s3_run/')
                call_system('aws s3 cp {s3_location} /tmp/s3_run/'.format(s3_location=s3_location))
                uncompress_command = None
                if s3_filename.endswith('.zip'):
                    uncompress_command = 'unzip'
                if s3_filename.endswith('.tgz'):
                    uncompress_command = 'tar -zxf'
                call_system('cd /tmp/s3_run && {uncompress_command} {s3_filename}'.format(s3_filename=s3_filename,
                                                                                          uncompress_command=uncompress_command))
                call_system('cp /tmp/s3_run/*/NIST/*.ttl {destination}/task2_kb.ttl'.format(destination=sparql_kb_input))
                call_system('rm -rf /tmp/s3_run')
                # get the file from s3
                # place it in the SPARQL-KB-input directory
        else:
            call_system('cp {input}/task2_kb.ttl {destination}'.format(input=args.input, destination=sparql_kb_input))
            # place the task2_kb.ttl in the SPARQL-KB-input directory

    #############################################################################################
    # apply sparql queries
    #############################################################################################

    record_and_display_message(logger, 'Applying SPARQL queries.')
    graphdb_bin = '/opt/graphdb/dist/bin'
    graphdb = '{}/graphdb'.format(graphdb_bin)
    loadrdf = '{}/loadrdf'.format(graphdb_bin)
    verdi = '/opt/sparql-evaluation'
    jar = '{}/sparql-evaluation-1.0.0-SNAPSHOT-all.jar'.format(verdi)
    config = '{}/config/Local-config.ttl'.format(verdi)
    properties = '{}/config/Local-config.properties'.format(verdi)
    intermediate = '{}/intermediate'.format(sparql_output)
    queries = '{}/queries'.format(args.output)

    # copy queries to be applied
    record_and_display_message(logger, 'Copying SPARQL queries to be applied.')
    call_system('mkdir {queries}'.format(queries=queries))
    call_system('cp /data/queries/AIDA_P2_TA2_*.rq {queries}'.format(task=args.task, queries=queries))

    record_and_display_message(logger, 'Applying queries to task2_kb.ttl ... ')
    # create the intermediate directory
    logger.record_event('DEFAULT_INFO', 'Creating {}.'.format(intermediate))
    call_system('mkdir -p {}'.format(intermediate))
    # load KB into GraphDB
    logger.record_event('DEFAULT_INFO', 'Loading task2_kb.ttl into GraphDB.')
    input_kb = '{sparql_kb_input}/task2_kb.ttl'.format(sparql_kb_input=sparql_kb_input)
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
    # move output out of intermediate into the output corresponding to the KB
    logger.record_event('DEFAULT_INFO', 'Moving output out of the intermediate directory')
    call_system('mv {intermediate}/*/* {output}'.format(intermediate=intermediate,
                                                        output=sparql_output))
    # remove intermediate directory
    logger.record_event('DEFAULT_INFO', 'Removing the intermediate directory.')
    call_system('rm -rf {}'.format(intermediate))
    # stop GraphDB
    logger.record_event('DEFAULT_INFO', 'Stopping GraphDB.')
    call_system('pkill -9 -f graphdb')

    #############################################################################################
    # Validate SPARQL output
    #############################################################################################

    record_and_display_message(logger, 'Validating SPARQL output.')

    log_file = '{logs_directory}/validate-responses.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3 validate_responses.py \
            --log {log_file} \
            --task task2 \
            {log_specifications} \
            {ontology_type_mappings} \
            {slotname_mappings} \
            {encoding_modality} \
            {coredocs} \
            {parent_children} \
            {sentence_boundaries} \
            {image_boundaries} \
            {keyframe_boundaries} \
            {video_boundaries} \
            {run_id} \
            {sparql_output} \
            {sparql_valid_output}'.format(python_scripts=python_scripts,
                                          log_file=log_file,
                                          log_specifications=log_specifications,
                                          ontology_type_mappings=ontology_type_mappings,
                                          slotname_mappings=slotname_mappings,
                                          encoding_modality=encoding_modality,
                                          coredocs=coredocs,
                                          parent_children=parent_children,
                                          sentence_boundaries=sentence_boundaries,
                                          image_boundaries=image_boundaries,
                                          keyframe_boundaries=keyframe_boundaries,
                                          video_boundaries=video_boundaries,
                                          run_id=args.run,
                                          sparql_output=sparql_output,
                                          sparql_valid_output=sparql_valid_output)
    call_system(cmd)

    num_errors = 0
    with open(log_file) as f:
        for line in f.readlines():
            if 'ERROR' in line:
                num_errors += 1

    if num_errors:
        print('\nSPARQL output had {} error(s).\n'.format(num_errors))
    else:
        print('\nSPARQL output had no errors.\n')

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
    parser.add_argument('-t', '--task', default='task2', help='Specify the task in order to apply relevant queries (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__,  help='Print version number and exit')
    args = parser.parse_args()
    main(args)
