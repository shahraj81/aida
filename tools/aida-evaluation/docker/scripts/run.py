"""
Script for AIDA evaluation pipeline that generates scores starting from KBs.

This version of the scorer works with M36 practice data.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "2019.1.0"
__date__    = "21 Aug 2020"

from logger import Logger
import argparse
import json
import os
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def call_system(cmd):
    cmd = ' '.join(cmd.split())
    print("running system command: '{}'".format(cmd))
    os.system(cmd)

def get_num_problems(logs_directory):
    num_errors = 0
    for filename in os.listdir(logs_directory):
        filepath = '{}/{}'.format(logs_directory, filename)
        fh = open(filepath)
        for line in fh.readlines():
            if 'ERROR' in line:
                num_errors += 1
        fh.close()
    return num_errors

def generate_results_file(logs_directory):
    metrics = {
        'ArgumentMetricV1_F1'  : 'ArgumentMetricV1-scores.txt',
        'ArgumentMetricV2_F1'  : 'ArgumentMetricV2-scores.txt',
        'CoreferenceMetric_F1' : 'CoreferenceMetric-scores.txt',
        'TemporalMetric_S'     : 'TemporalMetric-scores.txt',
        'TypeMetric_F1'        : 'TypeMetric-scores.txt',
        'FrameMetric_F1'       : 'FrameMetric-scores.txt'
        }

    scores = {}

    for metric in metrics:
        scores[metric] = 0
        filename = '{output}/scores/{filename}'.format(output=args.output,
                                                       filename=metrics[metric])
        if os.path.exists(filename):
            file_handle = open(filename, "r")
            lines = file_handle.readlines()
            summary_line = lines[-1]
            file_handle.close()
            scores[metric] = summary_line.split()[-1]

    output = {'scores' : [
                            {
                                'CoreferenceMetric_F1': scores['CoreferenceMetric_F1'],
                                'TypeMetric_F1'       : scores['TypeMetric_F1'],
                                'TemporalMetric_S'    : scores['TemporalMetric_S'],
                                'ArgumentMetricV1_F1' : scores['ArgumentMetricV1_F1'],
                                'ArgumentMetricV2_F1' : scores['ArgumentMetricV2_F1'],
                                'FrameMetric_F1'      : scores['FrameMetric_F1'],
                                'Total'               : scores['FrameMetric_F1'],
                                'Errors'              : get_num_problems(logs_directory)
                            }
                         ]
            }

    outputdir = "/score/"
    with open(outputdir + 'results.json', 'w') as fp:
        json.dump(output, fp, indent=4, sort_keys=True)

def record_and_display_message(logger, message):
    print("-------------------------------------------------------")
    print(message)
    print("-------------------------------------------------------")
    logger.record_event('DEFAULT_INFO', message)

def main(args):
    """
    The main program runs the following steps in the AIDA evaluation pipeline:

        (1) Apply SPARQL queries to KBs,
        (2) Clean SPARQL output,
        (3) Validate cleaned SPARQL output,
        (4) Filter validated SPARQL output to retain responses that were in the annotated regions,
        (5) Align clusters in system responses with those in the gold M18 annotations,
        (6) Generate scores.

    Note that SPARQL queries are applied only to those KBs that came from the
    set of core documents included in M18 annotations.
    """

    #############################################################################################
    # AUX-data
    #############################################################################################

    python_scripts          = '/scripts/aida/python'
    log_specifications      = '{}/input/aux_data/log_specifications.txt'.format(python_scripts)
    logs_directory          = '{output}/{logs}'.format(output=args.output, logs=args.logs)
    run_log_file            = '{logs_directory}/run.log'.format(logs_directory=logs_directory)
    ontology_type_mappings  = '/data/AUX-data/AIDA_Annotation_Ontology_Phase2_V1.1_typemappings.tab'
    slotname_mappings       = '/data/AUX-data/AIDA_Annotation_Ontology_Phase2_V1.1_slotnamemappings.tab'
    encoding_modality       = '/data/AUX-data/encoding_modality.txt'
    coredocs_29             = '/data/AUX-data/LDC2020E11.coredocs-29.txt'
    parent_children         = '/data/AUX-data/LDC2020E11.parent_children.tsv'
    sentence_boundaries     = '/data/AUX-data/LDC2020E11.sentence_boundaries.txt'
    image_boundaries        = '/data/AUX-data/LDC2020E11.image_boundaries.txt'
    keyframe_boundaries     = '/data/AUX-data/LDC2020E11.keyframe_boundaries.txt'
    video_boundaries        = '/data/AUX-data/LDC2020E11.video_boundaries.txt'
    annotated_regions       = '/data/AUX-data/LDC2020E11.annotated_regions.txt'
    sparql_kb_input         = '{output}/SPARQL-KB-input'.format(output=args.output)
    sparql_output           = '{output}/SPARQL-output'.format(output=args.output)
    sparql_clean_output     = '{output}/SPARQL-CLEAN-output'.format(output=args.output)
    sparql_filtered_output  = '{output}/SPARQL-FILTERED-output'.format(output=args.output)
    sparql_valid_output     = '{output}/SPARQL-VALID-output'.format(output=args.output)
    alignment               = '{output}/alignment'.format(output=args.output)
    similarities            = '{output}/similarities'.format(output=args.output)
    scores                  = '{output}/scores'.format(output=args.output)

    gold_filtered_responses = '/data/gold/SPARQL-FILTERED-output'

    #############################################################################################
    # pull latest copy of code from git
    #############################################################################################

    call_system('cd {python_scripts} && git pull'.format(python_scripts=python_scripts))

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

    call_system('mkdir {logs_directory}'.format(logs_directory=logs_directory))
    logger = Logger(run_log_file, args.spec, sys.argv)

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
        generate_results_file(logs_directory)
        exit(ALLOK_EXIT_CODE)

    # load core documents
    file_handle = open(coredocs_29, 'r')
    lines = file_handle.readlines()
    file_handle.close()
    coredocs = [d.strip() for d in lines[1:]]
    for kb in kbs:
        if kbs[kb] and kb not in coredocs:
            kbs[kb] = 0

    # copy valid input KBs for querying
    # restrict to core-18 documents
    record_and_display_message(logger, 'Copying valid input KBs, restricted to core documents, for applying SPARQL queries.')
    call_system('mkdir {sparql_kb_input}'.format(sparql_kb_input=sparql_kb_input))
    for kb in kbs:
        if kbs[kb] and kb in coredocs:
            logger.record_event('DEFAULT_INFO', 'Copying {}.ttl'.format(kb))
            call_system('cp {input}/{kb}.ttl {sparql_kb_input}'.format(input=args.input, sparql_kb_input=sparql_kb_input, kb=kb))

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
    call_system('cp /data/queries/*.rq {queries}'.format(task=args.task, queries=queries))

    num_total = len([d for d in kbs if kbs[d] == 1])
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
        input_kb = '{sparql_kb_input}/{kb}.ttl'.format(sparql_kb_input=sparql_kb_input, kb=kb)
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
    # Clean SPARQL output
    #############################################################################################

    record_and_display_message(logger, 'Cleaning SPARQL output.')

    python_scripts = '/scripts/aida/python'

    cmd = 'cd {python_scripts} && \
            python3 clean_sparql_output.py \
            {log_specifications} \
            {sparql_output} \
            {sparql_clean_output}'.format(python_scripts=python_scripts,
                                          log_specifications=log_specifications,
                                          sparql_output = sparql_output,
                                          sparql_clean_output = sparql_clean_output)
    call_system(cmd)

    #############################################################################################
    # Validate SPARQL output
    #############################################################################################

    record_and_display_message(logger, 'Validating SPARQL output.')

    log_file = '{logs_directory}/validate-responses.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3 validate_responses.py \
            --log {log_file} \
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
            {sparql_clean_output} \
            {sparql_valid_output}'.format(python_scripts=python_scripts,
                                          log_file=log_file,
                                          log_specifications=log_specifications,
                                          ontology_type_mappings=ontology_type_mappings,
                                          slotname_mappings=slotname_mappings,
                                          encoding_modality=encoding_modality,
                                          coredocs=coredocs_29,
                                          parent_children=parent_children,
                                          sentence_boundaries=sentence_boundaries,
                                          image_boundaries=image_boundaries,
                                          keyframe_boundaries=keyframe_boundaries,
                                          video_boundaries=video_boundaries,
                                          run_id=args.run,
                                          sparql_clean_output=sparql_clean_output,
                                          sparql_valid_output=sparql_valid_output)
    call_system(cmd)

    #############################################################################################
    # Filter SPARQL output
    #############################################################################################

    record_and_display_message(logger, 'Filtering SPARQL output.')

    log_file = '{logs_directory}/filter-responses.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3 filter_responses.py \
            --log {log_file} \
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
            {annotated_regions} \
            {run_id} \
            {sparql_valid_output} \
            {sparql_filtered_output}'.format(python_scripts=python_scripts,
                                             log_file=log_file,
                                             log_specifications=log_specifications,
                                             ontology_type_mappings=ontology_type_mappings,
                                             slotname_mappings=slotname_mappings,
                                             encoding_modality=encoding_modality,
                                             coredocs=coredocs_29,
                                             parent_children=parent_children,
                                             sentence_boundaries=sentence_boundaries,
                                             image_boundaries=image_boundaries,
                                             keyframe_boundaries=keyframe_boundaries,
                                             video_boundaries=video_boundaries,
                                             annotated_regions=annotated_regions,
                                             run_id=args.run,
                                             sparql_valid_output=sparql_valid_output,
                                             sparql_filtered_output=sparql_filtered_output)
    call_system(cmd)

    #############################################################################################
    # Aligning clusters
    #############################################################################################

    record_and_display_message(logger, 'Aligning clusters.')

    log_file = '{logs_directory}/align-clusters.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3 align_clusters.py \
            --log {log_file} \
            {log_specifications} \
            {encoding_modality} \
            {coredocs} \
            {parent_children} \
            {sentence_boundaries} \
            {image_boundaries} \
            {keyframe_boundaries} \
            {video_boundaries} \
            {annotated_regions} \
            {gold_filtered_responses} \
            {sparql_filtered_output} \
            {similarities} \
            {alignment}'.format(python_scripts=python_scripts,
                                log_file=log_file,
                                log_specifications=log_specifications,
                                encoding_modality=encoding_modality,
                                coredocs=coredocs_29,
                                parent_children=parent_children,
                                sentence_boundaries=sentence_boundaries,
                                image_boundaries=image_boundaries,
                                keyframe_boundaries=keyframe_boundaries,
                                video_boundaries=video_boundaries,
                                annotated_regions=annotated_regions,
                                gold_filtered_responses=gold_filtered_responses,
                                sparql_filtered_output=sparql_filtered_output,
                                similarities=similarities,
                                alignment=alignment)
    call_system(cmd)

    #############################################################################################
    # generate scores
    #############################################################################################

    record_and_display_message(logger, 'Generating scores.')

    log_file = '{logs_directory}/score_submission.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3 score_submission.py \
            --log {log_file} \
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
            {annotated_regions} \
            {gold_filtered_responses} \
            {sparql_filtered_output} \
            {alignment} \
            {similarities} \
            {run_id} \
            {scores}'.format(python_scripts=python_scripts,
                                log_file=log_file,
                                log_specifications=log_specifications,
                                ontology_type_mappings = ontology_type_mappings,
                                slotname_mappings=slotname_mappings,
                                encoding_modality=encoding_modality,
                                coredocs=coredocs_29,
                                parent_children=parent_children,
                                sentence_boundaries=sentence_boundaries,
                                image_boundaries=image_boundaries,
                                keyframe_boundaries=keyframe_boundaries,
                                video_boundaries=video_boundaries,
                                annotated_regions=annotated_regions,
                                gold_filtered_responses=gold_filtered_responses,
                                sparql_filtered_output=sparql_filtered_output,
                                similarities=similarities,
                                alignment=alignment,
                                run_id=args.run,
                                scores=scores)
    call_system(cmd)

    # generate results.json file
    record_and_display_message(logger, 'Generating results.json file.')
    generate_results_file(logs_directory)
    record_and_display_message(logger, 'Done.')

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
