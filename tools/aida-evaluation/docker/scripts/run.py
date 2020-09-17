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

def generate_results_file(logger, logs_directory):

    metric_classes_specs = """
        # Filename                     Metric                              ColumnValuePairs               ScoreColumn
        #
        # ---
        # ArgumentMetricV1
        #
          ArgumentMetricV1-scores.txt  ArgumentMetricV1_F1                 Language:ALL,Metatype:ALL      F1

          ArgumentMetricV1-scores.txt  ArgumentMetricV1_Events_F1          Language:ALL,Metatype:Event    F1
          ArgumentMetricV1-scores.txt  ArgumentMetricV1_Relations_F1       Language:ALL,Metatype:Relation F1

          ArgumentMetricV1-scores.txt  ArgumentMetricV1_ENG_F1             Language:ENG,Metatype:ALL      F1
          ArgumentMetricV1-scores.txt  ArgumentMetricV1_ENG_Events_F1      Language:ENG,Metatype:Event    F1
          ArgumentMetricV1-scores.txt  ArgumentMetricV1_ENG_Relations_F1   Language:ENG,Metatype:Relation F1

          ArgumentMetricV1-scores.txt  ArgumentMetricV1_RUS_F1             Language:RUS,Metatype:ALL      F1
          ArgumentMetricV1-scores.txt  ArgumentMetricV1_RUS_Events_F1      Language:RUS,Metatype:Event    F1
          ArgumentMetricV1-scores.txt  ArgumentMetricV1_RUS_Relations_F1   Language:RUS,Metatype:Relation F1

          ArgumentMetricV1-scores.txt  ArgumentMetricV1_SPA_F1             Language:SPA,Metatype:ALL      F1
          ArgumentMetricV1-scores.txt  ArgumentMetricV1_SPA_Events_F1      Language:SPA,Metatype:Event    F1
          ArgumentMetricV1-scores.txt  ArgumentMetricV1_SPA_Relations_F1   Language:SPA,Metatype:Relation F1

        # ---
        # ArgumentMetricV2
        #
          ArgumentMetricV2-scores.txt  ArgumentMetricV2_F1                 Language:ALL,Metatype:ALL      F1

          ArgumentMetricV2-scores.txt  ArgumentMetricV2_Events_F1          Language:ALL,Metatype:Event    F1
          ArgumentMetricV2-scores.txt  ArgumentMetricV2_Relations_F1       Language:ALL,Metatype:Relation F1

          ArgumentMetricV2-scores.txt  ArgumentMetricV2_ENG_F1             Language:ENG,Metatype:ALL      F1
          ArgumentMetricV2-scores.txt  ArgumentMetricV2_ENG_Events_F1      Language:ENG,Metatype:Event    F1
          ArgumentMetricV2-scores.txt  ArgumentMetricV2_ENG_Relations_F1   Language:ENG,Metatype:Relation F1

          ArgumentMetricV2-scores.txt  ArgumentMetricV2_RUS_F1             Language:RUS,Metatype:ALL      F1
          ArgumentMetricV2-scores.txt  ArgumentMetricV2_RUS_Events_F1      Language:RUS,Metatype:Event    F1
          ArgumentMetricV2-scores.txt  ArgumentMetricV2_RUS_Relations_F1   Language:RUS,Metatype:Relation F1

          ArgumentMetricV2-scores.txt  ArgumentMetricV2_SPA_F1             Language:SPA,Metatype:ALL      F1
          ArgumentMetricV2-scores.txt  ArgumentMetricV2_SPA_Events_F1      Language:SPA,Metatype:Event    F1
          ArgumentMetricV2-scores.txt  ArgumentMetricV2_SPA_Relations_F1   Language:SPA,Metatype:Relation F1

        # ---
        # CoreferenceMetric
        #
          CoreferenceMetric-scores.txt CoreferenceMetric_F1                Language:ALL,Metatype:ALL      F1

          CoreferenceMetric-scores.txt CoreferenceMetric_Events_F1         Language:ALL,Metatype:Event    F1
          CoreferenceMetric-scores.txt CoreferenceMetric_Entities_F1       Language:ALL,Metatype:Entity   F1

          CoreferenceMetric-scores.txt CoreferenceMetric_ENG_F1            Language:ENG,Metatype:ALL      F1
          CoreferenceMetric-scores.txt CoreferenceMetric_ENG_Events_F1     Language:ENG,Metatype:Event    F1
          CoreferenceMetric-scores.txt CoreferenceMetric_ENG_Entities_F1   Language:ENG,Metatype:Entity   F1

          CoreferenceMetric-scores.txt CoreferenceMetric_RUS_F1            Language:RUS,Metatype:ALL      F1
          CoreferenceMetric-scores.txt CoreferenceMetric_RUS_Events_F1     Language:RUS,Metatype:Event    F1
          CoreferenceMetric-scores.txt CoreferenceMetric_RUS_Entities_F1   Language:RUS,Metatype:Entity   F1

          CoreferenceMetric-scores.txt CoreferenceMetric_SPA_F1            Language:SPA,Metatype:ALL      F1
          CoreferenceMetric-scores.txt CoreferenceMetric_SPA_Events_F1     Language:SPA,Metatype:Event    F1
          CoreferenceMetric-scores.txt CoreferenceMetric_SPA_Entities_F1   Language:SPA,Metatype:Entity   F1

        # ---
        # TemporalMetric
        #
          TemporalMetric-scores.txt    TemporalMetric_S                    Language:ALL,Metatype:ALL      Similarity

          TemporalMetric-scores.txt    TemporalMetric_Events_S             Language:ALL,Metatype:Event    Similarity
          TemporalMetric-scores.txt    TemporalMetric_Relations_S          Language:ALL,Metatype:Relation Similarity

          TemporalMetric-scores.txt    TemporalMetric_ENG_S                Language:ENG,Metatype:ALL      Similarity
          TemporalMetric-scores.txt    TemporalMetric_ENG_Events_S         Language:ENG,Metatype:Event    Similarity
          TemporalMetric-scores.txt    TemporalMetric_ENG_Relations_S      Language:ENG,Metatype:Relation Similarity

          TemporalMetric-scores.txt    TemporalMetric_RUS_S                Language:RUS,Metatype:ALL      Similarity
          TemporalMetric-scores.txt    TemporalMetric_RUS_Events_S         Language:RUS,Metatype:Event    Similarity
          TemporalMetric-scores.txt    TemporalMetric_RUS_Relations_S      Language:RUS,Metatype:Relation Similarity

          TemporalMetric-scores.txt    TemporalMetric_SPA_S                Language:SPA,Metatype:ALL      Similarity
          TemporalMetric-scores.txt    TemporalMetric_SPA_Events_S         Language:SPA,Metatype:Event    Similarity
          TemporalMetric-scores.txt    TemporalMetric_SPA_Relations_S      Language:SPA,Metatype:Relation Similarity

        # ---
        # TypeMetric
        #
          TypeMetric-scores.txt        TypeMetric_F1                       Language:ALL,Metatype:ALL      F1

          TypeMetric-scores.txt        TypeMetric_Events_F1                Language:ALL,Metatype:Event    F1
          TypeMetric-scores.txt        TypeMetric_Entities_F1              Language:ALL,Metatype:Entity   F1

          TypeMetric-scores.txt        TypeMetric_ENG_F1                   Language:ENG,Metatype:ALL      F1
          TypeMetric-scores.txt        TypeMetric_ENG_Events_F1            Language:ENG,Metatype:Event    F1
          TypeMetric-scores.txt        TypeMetric_ENG_Entities_F1          Language:ENG,Metatype:Entity   F1

          TypeMetric-scores.txt        TypeMetric_RUS_F1                   Language:RUS,Metatype:ALL      F1
          TypeMetric-scores.txt        TypeMetric_RUS_Events_F1            Language:RUS,Metatype:Event    F1
          TypeMetric-scores.txt        TypeMetric_RUS_Entities_F1          Language:RUS,Metatype:Entity   F1

          TypeMetric-scores.txt        TypeMetric_SPA_F1                   Language:SPA,Metatype:ALL      F1
          TypeMetric-scores.txt        TypeMetric_SPA_Events_F1            Language:SPA,Metatype:Event    F1
          TypeMetric-scores.txt        TypeMetric_SPA_Entities_F1          Language:SPA,Metatype:Entity   F1

        # ---
        # FrameMetric
        #
          FrameMetric-scores.txt       FrameMetric_F1                      Language:ALL,Metatype:ALL      F1

          FrameMetric-scores.txt       FrameMetric_Events_F1               Language:ALL,Metatype:Event    F1
          FrameMetric-scores.txt       FrameMetric_Relations_F1            Language:ALL,Metatype:Relation F1

          FrameMetric-scores.txt       FrameMetric_ENG_F1                  Language:ENG,Metatype:ALL      F1
          FrameMetric-scores.txt       FrameMetric_ENG_Events_F1           Language:ENG,Metatype:Event    F1
          FrameMetric-scores.txt       FrameMetric_ENG_Relations_F1        Language:ENG,Metatype:Relation F1

          FrameMetric-scores.txt       FrameMetric_RUS_F1                  Language:RUS,Metatype:ALL      F1
          FrameMetric-scores.txt       FrameMetric_RUS_Events_F1           Language:RUS,Metatype:Event    F1
          FrameMetric-scores.txt       FrameMetric_RUS_Relations_F1        Language:RUS,Metatype:Relation F1

          FrameMetric-scores.txt       FrameMetric_SPA_F1                  Language:SPA,Metatype:ALL      F1
          FrameMetric-scores.txt       FrameMetric_SPA_Events_F1           Language:SPA,Metatype:Event    F1
          FrameMetric-scores.txt       FrameMetric_SPA_Relations_F1        Language:SPA,Metatype:Relation F1

    """

    metric_column_value_pairs = {}
    metric_classes = {}
    for line in metric_classes_specs.split('\n'):
        line = line.strip()
        if line == '': continue
        if line.startswith('#'): continue
        filename, metricname, column_value_pairs, score_columnname = line.split()
        metric_classname = filename.split('-')[0]
        metric_column_value_pair = '{metric_classname}:{column_value_pairs}'.format(metric_classname=metric_classname,
                                                                                   column_value_pairs=','.join(sorted(column_value_pairs.split(','))))
        if metric_column_value_pair in metric_column_value_pairs:
            logger.record_event('DEFAULT_CRITICAL_ERROR', 'Duplicate column-value pair \'{}\' for metric-class: \'{}\''.format(metric_classname,
                                                                                                                               column_value_pairs))
        metric_column_value_pairs[metric_column_value_pair] = 1
        if metric_classname not in metric_classes:
            metric_class = {'Filename': filename, 'Metrics': {}}
            metric_classes[metric_classname] = metric_class
        metric_class = metric_classes[metric_classname]
        columns = {}
        for column_value_pair in column_value_pairs.split(','):
            column, value = column_value_pair.split(':')
            columns[column] = value
        metric = {
            'Columns': columns,
            'ScoreColumn': score_columnname
            }
        if metricname in metric_class['Metrics']:
            logger.record_event('DEFAULT_CRITICAL_ERROR', 'Duplicate metricname: {} (expected to be unique)'.format(metricname) )
        metric_class['Metrics'][metricname] = metric

    scores = {}

    exit_code = ALLOK_EXIT_CODE

    for metric_class in metric_classes.values():
        filename = '{output}/scores/{filename}'.format(output=args.output,
                                                       filename=metric_class['Filename'])
        summary_scores = []
        if os.path.exists(filename):
            file_handle = open(filename, "r")
            lines = file_handle.readlines()
            columns = lines[0].strip().split()
            for line in [l for l in lines if 'Summary' in l]:
                line.strip()
                values = line.split()
                for i in range(len(columns) - len(values)):
                    values.insert(len(values)-1, '')
                score = {columns[i]:values[i] for i in range(len(columns))}
                summary_scores.append(score)
        else:
            exit_code = ERROR_EXIT_CODE

        metrics = metric_class['Metrics']
        for metric_name in metrics:
            scores[metric_name] = 0
            specs = metrics[metric_name]
            for score in [s for s in summary_scores]:
                num_columns = len(specs['Columns'])
                num_matched = 0
                for column_name, column_value in specs['Columns'].items():
                    if column_value == score[column_name]:
                        num_matched += 1
                if num_columns == num_matched:
                    scores[metric_name] = score[specs['ScoreColumn']]
                    if 'Metric' in score:
                        logger.record_event('DEFAULT_CRITICAL_ERROR', 'Attempting to bind score to {} which was already bound to {}'.format(metric_name, score['Metric']))
                    score['Metric'] = metric_name

    num_problems, problem_stats = get_problems(logs_directory)

    fatal_error = 'Yes' if exit_code == ERROR_EXIT_CODE else 'No'

    scores['Total'] = scores['FrameMetric_F1']
    scores['Errors'] = num_problems
    scores['ErrorStats'] = problem_stats
    scores['FatalError'] = fatal_error

    output = {'scores' : [
                            scores
                         ]
            }

    outputdir = "/score/"
    with open(outputdir + 'results.json', 'w') as fp:
        json.dump(output, fp, indent=4, sort_keys=True)

    exit_message = 'Done.'
    if exit_code == ERROR_EXIT_CODE:
        exit_message = 'Fatal error encountered.'
    record_and_display_message(logger, exit_message)

    exit(exit_code)

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
    coredocs_xx             = '/data/AUX-data/LDC2020E11.coredocs-xx.txt'
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
    items = [f for f in os.listdir(args.input)]

    performer = None

    num_files = 0
    num_directories = 0

    open_performer_files = ['AIDA_P2_TA1_AM_A0001.rq.tsv', 'AIDA_P2_TA1_CM_A0001.rq.tsv', 'AIDA_P2_TA1_TM_A0001.rq.tsv']

    for item in items:
        if not item.endswith('.ttl'): continue
        if item.startswith('.'): continue
        if os.path.isfile(os.path.join(args.input, item)):
            num_files += 1
            if performer is None or performer == 'AIDA':
                performer = 'AIDA'
            else:
                logger.record_event('UNKNOWN_PERFORMER_TYPE')
        elif os.path.isdir(os.path.join(args.input, item)):
            num_directories += 1
            if performer is None or performer == 'OPEN':
                performer = 'OPEN'
                expected_files = {f:0 for f in open_performer_files}
                for filename in os.listdir(os.path.join(args.input, item)):
                    if filename in expected_files:
                        pathname = '{}/{}'.format(args.input, item)
                        if os.path.isfile(os.path.join(pathname, filename)):
                            expected_files[filename] = 1
                for filename in expected_files:
                    if expected_files[filename] == 0:
                        logger.record_event('MISSING_OPEN_PERFORMER_FILE', pathname, filename)
                        generate_results_file(logger, logs_directory)
            else:
                logger.record_event('UNKNOWN_PERFORMER_TYPE')
                generate_results_file(logger, logs_directory)

    documents_in_submission = {}
    num_total_documents = 0
    num_invalid_documents = 0
    for item in items:
        if item.endswith('.ttl'):
            documents_in_submission[item.replace('.ttl', '')] = 1
            num_total_documents = num_total_documents + 1
    for item in items:
        if item.endswith('-report.txt'):
            documents_in_submission[item.replace('-report.txt', '')] = 0
            num_invalid_documents = num_invalid_documents + 1
    num_valid_documents = num_total_documents - num_invalid_documents
    if performer == 'AIDA':
        logger.record_event('KB_STATS', num_total_documents, num_valid_documents, num_invalid_documents)

    # exit if no valid input KB
    if num_valid_documents == 0:
        logger.record_event('NOTHING_TO_SCORE')
        record_and_display_message(logger, 'Nothing to score.')
        generate_results_file(logger, logs_directory)

    # load core documents
    file_handle = open(coredocs_xx, 'r')
    lines = file_handle.readlines()
    file_handle.close()
    coredocs = [d.strip() for d in lines[1:]]
    for document_id in documents_in_submission:
        if documents_in_submission[document_id] and document_id not in coredocs:
            documents_in_submission[document_id] = 0

    # copy valid input KBs for querying
    # restrict to annotated documents
    if performer == 'AIDA':
        destination = sparql_kb_input
        record_and_display_message(logger, 'Copying valid input KBs, restricted to core documents, for applying SPARQL queries.')
    if performer == 'OPEN':
        destination = sparql_clean_output
        record_and_display_message(logger, 'Copying input corresponding to core documents for scoring.')
    call_system('mkdir {destination}'.format(destination=destination))
    for document_id in documents_in_submission:
        if documents_in_submission[document_id] and document_id in coredocs:
            logger.record_event('DEFAULT_INFO', 'Copying {}.ttl'.format(document_id))
            call_system('cp -r {input}/{document_id}.ttl {destination}'.format(input=args.input, destination=destination, document_id=document_id))

    #############################################################################################
    # apply sparql queries
    #############################################################################################

    if performer == 'AIDA':

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

        num_total = len([d for d in documents_in_submission if documents_in_submission[d] == 1])
        count = 0;
        for document_id in documents_in_submission:
            if documents_in_submission[document_id] == 0:
                continue
            count = count + 1
            record_and_display_message(logger, 'Applying queries to {document_id}.ttl ... {count} of {num_total}.'.format(count=count,
                                                                                                          num_total=num_total,
                                                                                                          document_id=document_id))
            # create the intermediate directory
            logger.record_event('DEFAULT_INFO', 'Creating {}.'.format(intermediate))
            call_system('mkdir -p {}'.format(intermediate))
            # load KB into GraphDB
            logger.record_event('DEFAULT_INFO', 'Loading {}.ttl into GraphDB.'.format(document_id))
            input_kb = '{sparql_kb_input}/{document_id}.ttl'.format(sparql_kb_input=sparql_kb_input, document_id=document_id)
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
            call_system('mkdir {sparql_output}/{document_id}.ttl'.format(sparql_output=sparql_output, document_id=document_id))
            # move output out of intermediate into the output corresponding to the KB
            logger.record_event('DEFAULT_INFO', 'Moving output out of the intermediate directory')
            call_system('mv {intermediate}/*/* {output}/{document_id}.ttl'.format(intermediate=intermediate,
                                                                              output=sparql_output,
                                                                              document_id=document_id))
            # remove intermediate directory
            logger.record_event('DEFAULT_INFO', 'Removing the intermediate directory.')
            call_system('rm -rf {}'.format(intermediate))
            # stop GraphDB
            logger.record_event('DEFAULT_INFO', 'Stopping GraphDB.')
            call_system('pkill -9 -f graphdb')

    #############################################################################################
    # Clean SPARQL output
    #############################################################################################

    if performer == 'AIDA':

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
                                          coredocs=coredocs_xx,
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
                                             coredocs=coredocs_xx,
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
                                coredocs=coredocs_xx,
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
                                coredocs=coredocs_xx,
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
    generate_results_file(logger, logs_directory)

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
