"""
Script for generating AIF from LDCs annotations
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "2019.0.1"
__date__    = "26 May 2020"

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
    """
    The main program applying SPARQL queries, validate responses, generate aggregate confidences, and scores.
    """

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

    # create the logs directory
    logs = '{output}/{logs}'.format(output=args.output, logs=args.logs)
    call_system('mkdir {logs}'.format(logs=logs))
    # create the logger
    log = '{logs}/run.log'.format(logs=logs)
    logger = Logger(log, args.spec, sys.argv)

    #############################################################################################
    # inspect the input directory
    #############################################################################################
    record_and_display_message(logger, 'Inspecting the input directory.')
    files = [f for f in os.listdir(args.input) if os.path.isfile(os.path.join(args.input, f))]
    kbs = {}
    num_total_kbs = 0
    num_invalid_kbs = 0
    for file in files:
        if file.endswith('.ttl'):
            kbs[file.replace('.ttl', '')] = 1
            num_total_kbs = num_total_kbs + 1
    for file in files:
        if file.endswith('-report.txt'):
            kbs[file.replace('-report.txt', '')] = 0
            num_invalid_kbs = num_invalid_kbs + 1
    num_valid_kbs = num_total_kbs - num_invalid_kbs
    logger.record_event('KB_STATS', num_total_kbs, num_valid_kbs, num_invalid_kbs)
    
    # exit if no valid input KB
    if num_valid_kbs == 0:
        record_and_display_message(logger, 'No valid KB received as input.')
        exit(ALLOK_EXIT_CODE)
    
    # copy valid input KBs for querying
    record_and_display_message(logger, 'Copying valid input KBs for applying SPARQL queries.')
    call_system('mkdir /score/SPARQL-KB-input')
    for kb in kbs:
        if kbs[kb]:
            logger.record_event('DEFAULT_INFO', 'Copying {}.ttl'.format(kb))
            call_system('cp {input}/{kb}.ttl {output}/SPARQL-KB-input'.format(input=args.input, output=args.output, kb=kb))
    
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
    sparql_output = '/score/SPARQL-output'
    intermediate = '{}/intermediate'.format(sparql_output)
    queries = '{}/queries'.format(args.output)
    
    # copy queries to be applied
    record_and_display_message(logger, 'Copying SPARQL queries to be applied.')
    call_system('mkdir {queries}'.format(queries=queries))
    call_system('cp /queries/{task}_*_queries/*.rq {queries}'.format(task=args.task, queries=queries))
    
    num_total = len(kbs)
    count = 0;
    for kb in kbs:
        if kbs[kb] == 0:
            continue
        count = count + 1
        record_and_display_message(logger, 'Applying queries to {kb}.ttl ... {count} of {num_total}.'.format(count=count,
                                                                                                      num_total=num_total,
                                                                                                      kb=kb))
        # create the intermediate directory
        logger.record_event('DEFAULT_INFO', 'Creating {}.'.format(intermediate))
        call_system('mkdir -p {}'.format(intermediate))
        # load KB into GraphDB
        logger.record_event('DEFAULT_INFO', 'Loading {}.ttl into GraphDB.'.format(kb))
        input_kb = '{output}/SPARQL-KB-input/{kb}.ttl'.format(output=args.output, kb=kb)
        call_system('{loadrdf} -c {config} -f -m parallel {input}'.format(loadrdf=loadrdf, config=config, input=input_kb))
        # start GraphDB
        logger.record_event('DEFAULT_INFO', 'Starting GraphDB')
        call_system('{graphdb} -d'.format(graphdb=graphdb))
        # wait for GraphDB
        call_system('sleep 5')
        # apply queries
        logger.record_event('DEFAULT_INFO', 'Applying queries')
        call_system('java -Xmx1024M -jar {jar} -c {properties} -q {queries} -o {intermediate}/'.format(jar=jar,
                                                                                      properties=properties,
                                                                                      queries=queries,
                                                                                      intermediate=intermediate))
        # generate the SPARQL output directory corresponding to the KB
        logger.record_event('DEFAULT_INFO', 'Creating SPARQL output directory corresponding to the KB')
        call_system('mkdir {sparql_output}/{kb}.ttl'.format(sparql_output=sparql_output, kb=kb))
        # move output out of intermediate into the output corresponding to the KB
        logger.record_event('DEFAULT_INFO', 'Moving output out of the intermediate directory')
        call_system('mv {intermediate}/*/* {output}/{kb}.ttl'.format(intermediate=intermediate,
                                                                          output=sparql_output,
                                                                          kb=kb))
        # remove intermediate directory
        logger.record_event('DEFAULT_INFO', 'Removing the intermediate directory.')
        call_system('rm -rf {}'.format(intermediate))
        # stop GraphDB
        logger.record_event('DEFAULT_INFO', 'Stopping GraphDB.')
        call_system('pkill -9 -f graphdb')
    
    #############################################################################################
    # validate SPARQL output
    #############################################################################################
    record_and_display_message(logger, 'Validating SPARQL output.')
    
    sparql_valid_output = '{output}/SPARQL-VALID-output'.format(output=args.output)
    validate_responses = '/scripts/aida/tools/validate-responses'
    mappings = '/AUX-data/LDC2019E42.parent_children.tsv'
    sentences = '/AUX-data/LDC2019E42.sentence_boundaries.txt'
    images = '/AUX-data/LDC2019E42.image_boundaries.txt'
    keyframes = '/AUX-data/LDC2019E42.keyframe_boundaries.txt'
    coredocs_all = '/AUX-data/LDC2019E42.coredocs-all.txt'
    
    # create directory for valid SPARQL output
    call_system('mkdir {sparql_valid_output}'.format(sparql_valid_output=sparql_valid_output))
    
    # checkout the right branch of the validator
    call_system('cd /scripts/aida && git pull && git checkout AIDAVR-v2019.0.3')
    
    # validate class and graph responses separately
    query_types = {'class':'TA1_CL', 'graph':'TA1_GR'}
    for query_type in query_types:
        log = '{logs}/validate-{query_type}-responses.log'.format(logs=logs, query_type=query_type)
        queries_dtd = '/queries/{}_query.dtd'.format(query_type)
        queries_xml = '/queries/task1_{}_queries.xml'.format(query_type)
        cmd = 'cd {validate_responses} && \
                perl -I . AIDA-ValidateResponses-MASTER.pl \
                -error_file {log} \
                {mappings} \
                {sentences} \
                {images} \
                {keyframes} \
                {queries_dtd} \
                {queries_xml} \
                {coredocs} \
                {run_id} \
                {sparql_output} \
                {sparql_valid_output}'.format(validate_responses=validate_responses,
                                              log = log,
                                              mappings=mappings,
                                              sentences=sentences,
                                              images=images,
                                              keyframes=keyframes,
                                              queries_dtd=queries_dtd,
                                              queries_xml=queries_xml,
                                              coredocs=coredocs_all,
                                              run_id=args.run,
                                              sparql_output=sparql_output,
                                              sparql_valid_output=sparql_valid_output)
        call_system(cmd)
    
    #############################################################################################
    # generate aggregate confidences
    #############################################################################################
    record_and_display_message(logger, 'Generating aggregate confidences.')
    
    sparql_ca_output = '{output}/SPARQL-CA-output'.format(output=args.output)
    aggregate_confidences = '/scripts/aida/tools/confidence-aggregation'
    
    # create directory for confidence aggregation output
    call_system('mkdir {sparql_ca_output}'.format(sparql_ca_output=sparql_ca_output))

    # checkout the right branch of the confidence aggregator
    call_system('cd /scripts/aida && git pull && git checkout AIDACA-v2019.0.2')
    
    for query_type in query_types:
        task_and_type_code = query_types[query_type]
        log = '{logs}/aggregate-{query_type}-confidences.log'.format(logs=logs, query_type=query_type)
        cmd = 'cd {aggregate_confidences} && \
                perl -I . AIDA-ConfidenceAggregation-MASTER.pl \
                -error_file {log} \
                {task_and_type_code} \
                {sparql_valid_output} \
                {sparql_ca_output}'.format(aggregate_confidences=aggregate_confidences,
                                           log = log,
                                           task_and_type_code=task_and_type_code,
                                           sparql_valid_output=sparql_valid_output,
                                           sparql_ca_output=sparql_ca_output)
        call_system(cmd)
    
    #############################################################################################
    # generate scores
    #############################################################################################
    record_and_display_message(logger, 'Generating scores.')
    score_responses = '/scripts/aida/tools/scorer'
    score_output = '{output}/scores'.format(output=args.output)
    coredocs_scorer = '/AUX-data/LDC2019E42.coredocs-18.txt'
    assessments = '/AUX-data/LDC2019R30_AIDA_Phase_1_Assessment_Results_V6.1'
    intermediate = '{output}/scores-intermediate'.format(output=args.output)
    # create directory for scorer output
    call_system('mkdir {score_output}'.format(score_output=score_output))    
    # checkout the right branch of the scorer
    call_system('cd /scripts/aida && git pull && git checkout AIDASR-v2019.2.2')
    
    for query_type in query_types:
        log = '{logs}/{query_type}-score.log'.format(logs=logs, query_type=query_type)
        queries_dtd = '/queries/{}_query.dtd'.format(query_type)
        queries_xml = '/queries/task1_{}_queries.xml'.format(query_type)
        query_ids = '/AUX-data/task1_{}_queryids.txt'.format(query_type)
        output_file = '{score_output}/{query_type}-score.txt'.format(score_output=score_output,
                                                                     query_type=query_type)
        cmd = 'cd {score_responses} && \
                perl -I . AIDA-Score-MASTER.pl \
                -error_file {log} \
                -runid {runid} \
                {coredocs} \
                {mappings} \
                {sentences} \
                {images} \
                {keyframes} \
                {query_ids} \
                {queries_dtd} \
                {queries_xml} \
                none \
                {assessments} \
                {sparql_valid_output} \
                {sparql_ca_output} \
                {intermediate} \
                {output_file}'.format(score_responses=score_responses,
                                      log=log,
                                      runid=args.run,
                                      coredocs=coredocs_scorer,
                                      mappings=mappings,
                                      sentences=sentences,
                                      images=images,
                                      keyframes=keyframes,
                                      query_ids=query_ids,
                                      queries_dtd=queries_dtd,
                                      queries_xml=queries_xml,
                                      assessments=assessments,
                                      sparql_valid_output=sparql_valid_output,
                                      sparql_ca_output=sparql_ca_output,
                                      intermediate=intermediate,
                                      output_file=output_file
                                      )
        call_system(cmd)
        # remove intermediate directory for scorer output
        call_system('rm -rf {intermediate}'.format(intermediate=intermediate))

    record_and_display_message(logger, 'Generating scores completed.')
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Apply SPARQL queries, validate responses, generate aggregate confidences, and scores.")
    parser.add_argument('-i', '--input', default='/evaluate',
                        help='Specify the input directory (default: %(default)s)')
    parser.add_argument('-l', '--logs', default='logs',
                        help='Specify the name of the logs directory to which different log files should be written (default: %(default)s)')
    parser.add_argument('-o', '--output', default='/score',
                        help='Specify the input directory (default: %(default)s)')
    parser.add_argument('-r', '--run', default='system',
                        help='Specify the run name (default: %(default)s)')
    parser.add_argument('-s', '--spec', default='/scripts/log_specifications.txt',
                        help='Specify the log specifications file (default: %(default)s)')
    parser.add_argument('-t', '--task', default='task1',
                        help='Specify the task in order to apply relevant queries (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, 
                        help='Print version number and exit')
    args = parser.parse_args()
    main(args)