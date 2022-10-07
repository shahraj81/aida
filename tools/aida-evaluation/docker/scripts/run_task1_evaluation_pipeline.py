"""
Script for AIDA evaluation pipeline that generates scores starting from KBs.

This version of the scorer works with M36 practice data.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "2019.1.0"
__date__    = "21 Aug 2020"

from logger import Logger
from multiprocessing import Pool
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

def get_metric_classes_specs():

    metric_classes_specs = """
        # Filename                       Metric                                      ColumnValuePairs               ScoreColumn
        #
        # ---
        # ArgumentMetricV3A1
        #
          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_TRFscore                 Language:ALL,Metatype:ALL      TRFscore

          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_Events_TRFscore          Language:ALL,Metatype:Event    TRFscore
          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_Relations_TRFscore       Language:ALL,Metatype:Relation TRFscore

          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_ENG_TRFscore             Language:ENG,Metatype:ALL      TRFscore
          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_ENG_Events_TRFscore      Language:ENG,Metatype:Event    TRFscore
          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_ENG_Relations_TRFscore   Language:ENG,Metatype:Relation TRFscore

          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_RUS_TRFscore             Language:RUS,Metatype:ALL      TRFscore
          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_RUS_Events_TRFscore      Language:RUS,Metatype:Event    TRFscore
          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_RUS_Relations_TRFscore   Language:RUS,Metatype:Relation TRFscore

          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_SPA_TRFscore             Language:SPA,Metatype:ALL      TRFscore
          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_SPA_Events_TRFscore      Language:SPA,Metatype:Event    TRFscore
          ArgumentMetricV3A1-scores.txt  ArgumentMetricV3A1_SPA_Relations_TRFscore   Language:SPA,Metatype:Relation TRFscore

        # ---
        # ArgumentMetricV3B1
        #
          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_TRFscore                 Language:ALL,Metatype:ALL      TRFscore

          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_Events_TRFscore          Language:ALL,Metatype:Event    TRFscore
          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_Relations_TRFscore       Language:ALL,Metatype:Relation TRFscore

          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_ENG_TRFscore             Language:ENG,Metatype:ALL      TRFscore
          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_ENG_Events_TRFscore      Language:ENG,Metatype:Event    TRFscore
          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_ENG_Relations_TRFscore   Language:ENG,Metatype:Relation TRFscore

          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_RUS_TRFscore             Language:RUS,Metatype:ALL      TRFscore
          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_RUS_Events_TRFscore      Language:RUS,Metatype:Event    TRFscore
          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_RUS_Relations_TRFscore   Language:RUS,Metatype:Relation TRFscore

          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_SPA_TRFscore             Language:SPA,Metatype:ALL      TRFscore
          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_SPA_Events_TRFscore      Language:SPA,Metatype:Event    TRFscore
          ArgumentMetricV3B1-scores.txt  ArgumentMetricV3B1_SPA_Relations_TRFscore   Language:SPA,Metatype:Relation TRFscore

        # ---
        # ArgumentMetricV3C1
        #
          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_TRFscore                 Language:ALL,Metatype:ALL      TRFscore

          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_Events_TRFscore          Language:ALL,Metatype:Event    TRFscore
          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_Relations_TRFscore       Language:ALL,Metatype:Relation TRFscore

          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_ENG_TRFscore             Language:ENG,Metatype:ALL      TRFscore
          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_ENG_Events_TRFscore      Language:ENG,Metatype:Event    TRFscore
          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_ENG_Relations_TRFscore   Language:ENG,Metatype:Relation TRFscore

          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_RUS_TRFscore             Language:RUS,Metatype:ALL      TRFscore
          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_RUS_Events_TRFscore      Language:RUS,Metatype:Event    TRFscore
          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_RUS_Relations_TRFscore   Language:RUS,Metatype:Relation TRFscore

          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_SPA_TRFscore             Language:SPA,Metatype:ALL      TRFscore
          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_SPA_Events_TRFscore      Language:SPA,Metatype:Event    TRFscore
          ArgumentMetricV3C1-scores.txt  ArgumentMetricV3C1_SPA_Relations_TRFscore   Language:SPA,Metatype:Relation TRFscore

        # ---
        # ArgumentMetricV3A2
        #
          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_TRFscore                 Language:ALL,Metatype:ALL      TRFscore

          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_Events_TRFscore          Language:ALL,Metatype:Event    TRFscore
          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_Relations_TRFscore       Language:ALL,Metatype:Relation TRFscore

          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_ENG_TRFscore             Language:ENG,Metatype:ALL      TRFscore
          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_ENG_Events_TRFscore      Language:ENG,Metatype:Event    TRFscore
          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_ENG_Relations_TRFscore   Language:ENG,Metatype:Relation TRFscore

          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_RUS_TRFscore             Language:RUS,Metatype:ALL      TRFscore
          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_RUS_Events_TRFscore      Language:RUS,Metatype:Event    TRFscore
          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_RUS_Relations_TRFscore   Language:RUS,Metatype:Relation TRFscore

          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_SPA_TRFscore             Language:SPA,Metatype:ALL      TRFscore
          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_SPA_Events_TRFscore      Language:SPA,Metatype:Event    TRFscore
          ArgumentMetricV3A2-scores.txt  ArgumentMetricV3A2_SPA_Relations_TRFscore   Language:SPA,Metatype:Relation TRFscore

        # ---
        # ArgumentMetricV3B2
        #
          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_TRFscore                 Language:ALL,Metatype:ALL      TRFscore

          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_Events_TRFscore          Language:ALL,Metatype:Event    TRFscore
          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_Relations_TRFscore       Language:ALL,Metatype:Relation TRFscore

          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_ENG_TRFscore             Language:ENG,Metatype:ALL      TRFscore
          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_ENG_Events_TRFscore      Language:ENG,Metatype:Event    TRFscore
          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_ENG_Relations_TRFscore   Language:ENG,Metatype:Relation TRFscore

          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_RUS_TRFscore             Language:RUS,Metatype:ALL      TRFscore
          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_RUS_Events_TRFscore      Language:RUS,Metatype:Event    TRFscore
          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_RUS_Relations_TRFscore   Language:RUS,Metatype:Relation TRFscore

          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_SPA_TRFscore             Language:SPA,Metatype:ALL      TRFscore
          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_SPA_Events_TRFscore      Language:SPA,Metatype:Event    TRFscore
          ArgumentMetricV3B2-scores.txt  ArgumentMetricV3B2_SPA_Relations_TRFscore   Language:SPA,Metatype:Relation TRFscore

        # ---
        # ArgumentMetricV3C2
        #
          ArgumentMetricV3C2-scores.txt  ArgumentMetricV3C2_TRFscore                 Language:ALL,Metatype:ALL      TRFscore

          ArgumentMetricV3C2-scores.txt  ArgumentMetricV3C2_Events_TRFscore          Language:ALL,Metatype:Event    TRFscore
          ArgumentMetricV3C2-scores.txt  ArgumentMetricV3C2_Relations_TRFscore       Language:ALL,Metatype:Relation TRFscore

          ArgumentMetricV3C2-scores.txt  ArgumentMetricV3C2_ENG_TRFscore             Language:ENG,Metatype:ALL      TRFscore
          ArgumentMetricV3C2-scores.txt  ArgumentMetricV3C2_ENG_Events_TRFscore      Language:ENG,Metatype:Event    TRFscore
          ArgumentMetricV3C2-scores.txt  ArgumentMetricV3C2_ENG_Relations_TRFscore   Language:ENG,Metatype:Relation TRFscore

          ArgumentMetricV3C2-scores.txt  ArgumentMetricV3C2_RUS_TRFscore             Language:RUS,Metatype:ALL      TRFscore
          ArgumentMetricV3C2-scores.txt  ArgumentMetricV3C2_RUS_Events_TRFscore      Language:RUS,Metatype:Event    TRFscore
          ArgumentMetricV3C2-scores.txt  ArgumentMetricV3C2_RUS_Relations_TRFscore   Language:RUS,Metatype:Relation TRFscore

        # ---
        # CoreferenceMetric
        #
          CoreferenceMetric-scores.txt CoreferenceMetric_F1                          Language:ALL,Metatype:ALL      F1

          CoreferenceMetric-scores.txt CoreferenceMetric_Events_F1                   Language:ALL,Metatype:Event    F1
          CoreferenceMetric-scores.txt CoreferenceMetric_Entities_F1                 Language:ALL,Metatype:Entity   F1

          CoreferenceMetric-scores.txt CoreferenceMetric_ENG_F1                      Language:ENG,Metatype:ALL      F1
          CoreferenceMetric-scores.txt CoreferenceMetric_ENG_Events_F1               Language:ENG,Metatype:Event    F1
          CoreferenceMetric-scores.txt CoreferenceMetric_ENG_Entities_F1             Language:ENG,Metatype:Entity   F1

          CoreferenceMetric-scores.txt CoreferenceMetric_RUS_F1                      Language:RUS,Metatype:ALL      F1
          CoreferenceMetric-scores.txt CoreferenceMetric_RUS_Events_F1               Language:RUS,Metatype:Event    F1
          CoreferenceMetric-scores.txt CoreferenceMetric_RUS_Entities_F1             Language:RUS,Metatype:Entity   F1

          CoreferenceMetric-scores.txt CoreferenceMetric_SPA_F1                      Language:SPA,Metatype:ALL      F1
          CoreferenceMetric-scores.txt CoreferenceMetric_SPA_Events_F1               Language:SPA,Metatype:Event    F1
          CoreferenceMetric-scores.txt CoreferenceMetric_SPA_Entities_F1             Language:SPA,Metatype:Entity   F1

        # ---
        # TemporalMetric
        #
          TemporalMetric-scores.txt    TemporalMetric_S                              Language:ALL,Metatype:ALL      Similarity

          TemporalMetric-scores.txt    TemporalMetric_Events_S                       Language:ALL,Metatype:Event    Similarity
          TemporalMetric-scores.txt    TemporalMetric_Relations_S                    Language:ALL,Metatype:Relation Similarity

          TemporalMetric-scores.txt    TemporalMetric_ENG_S                          Language:ENG,Metatype:ALL      Similarity
          TemporalMetric-scores.txt    TemporalMetric_ENG_Events_S                   Language:ENG,Metatype:Event    Similarity
          TemporalMetric-scores.txt    TemporalMetric_ENG_Relations_S                Language:ENG,Metatype:Relation Similarity

          TemporalMetric-scores.txt    TemporalMetric_RUS_S                          Language:RUS,Metatype:ALL      Similarity
          TemporalMetric-scores.txt    TemporalMetric_RUS_Events_S                   Language:RUS,Metatype:Event    Similarity
          TemporalMetric-scores.txt    TemporalMetric_RUS_Relations_S                Language:RUS,Metatype:Relation Similarity

          TemporalMetric-scores.txt    TemporalMetric_SPA_S                          Language:SPA,Metatype:ALL      Similarity
          TemporalMetric-scores.txt    TemporalMetric_SPA_Events_S                   Language:SPA,Metatype:Event    Similarity
          TemporalMetric-scores.txt    TemporalMetric_SPA_Relations_S                Language:SPA,Metatype:Relation Similarity

        # ---
        # TypeMetricV4
        #
          TypeMetricV4-scores.txt        TypeMetricV4_S                              Language:ALL,Metatype:ALL      TypeSimilarity

          TypeMetricV4-scores.txt        TypeMetricV4_Events_S                       Language:ALL,Metatype:Event    TypeSimilarity
          TypeMetricV4-scores.txt        TypeMetricV4_Entities_S                     Language:ALL,Metatype:Entity   TypeSimilarity

          TypeMetricV4-scores.txt        TypeMetricV4_ENG_S                          Language:ENG,Metatype:ALL      TypeSimilarity
          TypeMetricV4-scores.txt        TypeMetricV4_ENG_Events_S                   Language:ENG,Metatype:Event    TypeSimilarity
          TypeMetricV4-scores.txt        TypeMetricV4_ENG_Entities_S                 Language:ENG,Metatype:Entity   TypeSimilarity

          TypeMetricV4-scores.txt        TypeMetricV4_RUS_S                          Language:RUS,Metatype:ALL      TypeSimilarity
          TypeMetricV4-scores.txt        TypeMetricV4_RUS_Events_S                   Language:RUS,Metatype:Event    TypeSimilarity
          TypeMetricV4-scores.txt        TypeMetricV4_RUS_Entities_S                 Language:RUS,Metatype:Entity   TypeSimilarity

          TypeMetricV4-scores.txt        TypeMetricV4_SPA_S                          Language:SPA,Metatype:ALL      TypeSimilarity
          TypeMetricV4-scores.txt        TypeMetricV4_SPA_Events_S                   Language:SPA,Metatype:Event    TypeSimilarity
          TypeMetricV4-scores.txt        TypeMetricV4_SPA_Entities_S                 Language:SPA,Metatype:Entity   TypeSimilarity

        # ---
        # FrameMetric
        #
          FrameMetric-scores.txt         FrameMetric_S                               Language:ALL,Metatype:ALL      AvgEdgeScore

          FrameMetric-scores.txt         FrameMetric_Events_S                        Language:ALL,Metatype:Event    AvgEdgeScore
          FrameMetric-scores.txt         FrameMetric_Relations_S                     Language:ALL,Metatype:Relation AvgEdgeScore

          FrameMetric-scores.txt         FrameMetric_ENG_S                           Language:ENG,Metatype:ALL      AvgEdgeScore
          FrameMetric-scores.txt         FrameMetric_ENG_Events_S                    Language:ENG,Metatype:Event    AvgEdgeScore
          FrameMetric-scores.txt         FrameMetric_ENG_Relations_S                 Language:ENG,Metatype:Relation AvgEdgeScore

          FrameMetric-scores.txt         FrameMetric_RUS_S                           Language:RUS,Metatype:ALL      AvgEdgeScore
          FrameMetric-scores.txt         FrameMetric_RUS_Events_S                    Language:RUS,Metatype:Event    AvgEdgeScore
          FrameMetric-scores.txt         FrameMetric_RUS_Relations_S                 Language:RUS,Metatype:Relation AvgEdgeScore

          FrameMetric-scores.txt         FrameMetric_SPA_S                           Language:SPA,Metatype:ALL      AvgEdgeScore
          FrameMetric-scores.txt         FrameMetric_SPA_Events_S                    Language:SPA,Metatype:Event    AvgEdgeScore
          FrameMetric-scores.txt         FrameMetric_SPA_Relations_S                 Language:SPA,Metatype:Relation AvgEdgeScore

        # ---
        # NegationMetricV1
        #
          NegationMetricV1-scores.txt    NegationMetricV1_F1                         Language:ALL,Metatype:ALL      F1

          NegationMetricV1-scores.txt    NegationMetricV1_Events_F1                  Language:ALL,Metatype:Event    F1
          NegationMetricV1-scores.txt    NegationMetricV1_Relations_F1               Language:ALL,Metatype:Relation F1

          NegationMetricV1-scores.txt    NegationMetricV1_ENG_F1                     Language:ENG,Metatype:ALL      F1
          NegationMetricV1-scores.txt    NegationMetricV1_ENG_Events_F1              Language:ENG,Metatype:Event    F1
          NegationMetricV1-scores.txt    NegationMetricV1_ENG_Relations_F1           Language:ENG,Metatype:Relation F1

          NegationMetricV1-scores.txt    NegationMetricV1_RUS_F1                     Language:RUS,Metatype:ALL      F1
          NegationMetricV1-scores.txt    NegationMetricV1_RUS_Events_F1              Language:RUS,Metatype:Event    F1
          NegationMetricV1-scores.txt    NegationMetricV1_RUS_Relations_F1           Language:RUS,Metatype:Relation F1

          NegationMetricV1-scores.txt    NegationMetricV1_SPA_F1                     Language:SPA,Metatype:ALL      F1
          NegationMetricV1-scores.txt    NegationMetricV1_SPA_Events_F1              Language:SPA,Metatype:Event    F1
          NegationMetricV1-scores.txt    NegationMetricV1_SPA_Relations_F1           Language:SPA,Metatype:Relation F1

        # ---
        # NegationMetricV2
        #
          NegationMetricV2-scores.txt    NegationMetricV2_F1                         Language:ALL,Metatype:ALL      F1

          NegationMetricV2-scores.txt    NegationMetricV2_Events_F1                  Language:ALL,Metatype:Event    F1
          NegationMetricV2-scores.txt    NegationMetricV2_Relations_F1               Language:ALL,Metatype:Relation F1

          NegationMetricV2-scores.txt    NegationMetricV2_ENG_F1                     Language:ENG,Metatype:ALL      F1
          NegationMetricV2-scores.txt    NegationMetricV2_ENG_Events_F1              Language:ENG,Metatype:Event    F1
          NegationMetricV2-scores.txt    NegationMetricV2_ENG_Relations_F1           Language:ENG,Metatype:Relation F1

          NegationMetricV2-scores.txt    NegationMetricV2_RUS_F1                     Language:RUS,Metatype:ALL      F1
          NegationMetricV2-scores.txt    NegationMetricV2_RUS_Events_F1              Language:RUS,Metatype:Event    F1
          NegationMetricV2-scores.txt    NegationMetricV2_RUS_Relations_F1           Language:RUS,Metatype:Relation F1

          NegationMetricV2-scores.txt    NegationMetricV2_SPA_F1                     Language:SPA,Metatype:ALL      F1
          NegationMetricV2-scores.txt    NegationMetricV2_SPA_Events_F1              Language:SPA,Metatype:Event    F1
          NegationMetricV2-scores.txt    NegationMetricV2_SPA_Relations_F1           Language:SPA,Metatype:Relation F1

    """
    return metric_classes_specs

def generate_results_file_and_exit(logger, logs_directory):
    metric_classes_specs = get_metric_classes_specs()
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
            for line in [l for l in lines if 'ALL-Macro' in l]:
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

    scores['RunID'] = args.run
    scores['Total'] = scores['FrameMetric_S']
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
        generate_results_file_and_exit(logger, logs_directory)
    ldc_package_id = runtypes[args.runtype]
    record_and_display_message(logger, 'Docker is using {} data for scoring'.format(args.runtype))

    thresholds = {
        'eng_iou_threshold': args.eng_iou_threshold,
        'spa_iou_threshold': args.spa_iou_threshold,
        'rus_iou_threshold': args.rus_iou_threshold,
        'image_iou_threshold': args.image_iou_threshold,
        'video_iou_threshold': args.video_iou_threshold,
        }

    for threshold_arg_name in thresholds:
        threshold = thresholds[threshold_arg_name]
        if not 0 <= threshold <= 1:
            logger.record_event('UNEXCPECTED_THRESHOLD', threshold_arg_name, threshold)
            generate_results_file_and_exit(logger, logs_directory)

    #############################################################################################
    # AUX-data
    #############################################################################################

    python_scripts          = '/scripts/aida/python'
    log_specifications      = '{}/input/aux_data/log_specifications.txt'.format(python_scripts)
    encoding_modality       = '/data/AUX-data/encoding_modality.txt'
    coredocs_xx             = '/data/AUX-data/{}.coredocs-xx.txt'.format(ldc_package_id)
    parent_children         = '/data/AUX-data/{}.parent_children.tsv'.format(ldc_package_id)
    sentence_boundaries     = '/data/AUX-data/{}.sentence_boundaries.txt'.format(ldc_package_id)
    image_boundaries        = '/data/AUX-data/{}.image_boundaries.txt'.format(ldc_package_id)
    keyframe_boundaries     = '/data/AUX-data/{}.keyframe_boundaries.txt'.format(ldc_package_id)
    video_boundaries        = '/data/AUX-data/{}.video_boundaries.txt'.format(ldc_package_id)
    annotation_tagset       = '/data/AUX-data/AIDA_TA1_Annotation_Tagset_Phase_3_External_V1.0.xlsx'
    dwd_overlay             = '/data/AUX-data/xpo_v5.1a.json'
    cache                   = '/data/AUX-data/cache.txt'
    sparql_kb_input         = '{output}/SPARQL-KB-input'.format(output=args.output)
    sparql_output           = '{output}/SPARQL-output'.format(output=args.output)
    sparql_clean_output     = '{output}/SPARQL-CLEAN-output'.format(output=args.output)
    sparql_filtered_output  = '{output}/SPARQL-FILTERED-output'.format(output=args.output)
    sparql_valid_output     = '{output}/SPARQL-VALID-output'.format(output=args.output)
    alignment               = '{output}/alignment'.format(output=args.output)
    similarities            = '{output}/similarities'.format(output=args.output)
    scores                  = '{output}/scores'.format(output=args.output)

    gold_valid_responses = '/data/gold/SPARQL-VALID-output'

    #############################################################################################
    # pull latest copy of code from git
    #############################################################################################

    call_system('cd {python_scripts} && git pull'.format(python_scripts=python_scripts))

    #############################################################################################
    # inspect the input directory
    #############################################################################################

    record_and_display_message(logger, 'Inspecting the input directory.')
    items = [f for f in os.listdir(args.input)]

    performer = None

    num_files = 0
    num_directories = 0

    open_performer_files = ['AIDA_P3_TA1_AM_A0001.rq.tsv', 'AIDA_P3_TA1_CM_A0001.rq.tsv', 'AIDA_P3_TA1_TM_A0001.rq.tsv']

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
                        generate_results_file_and_exit(logger, logs_directory)
            else:
                logger.record_event('UNKNOWN_PERFORMER_TYPE')
                generate_results_file_and_exit(logger, logs_directory)

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
        generate_results_file_and_exit(logger, logs_directory)

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
        loadrdf = '{}/importrdf load'.format(graphdb_bin)
        verdi = '/opt/sparql-evaluation'
        jar = '{}/sparql-evaluation-1.0.0-SNAPSHOT-all.jar'.format(verdi)
        config = '{}/config/Local-config.ttl'.format(verdi)
        properties = '{}/config/Local-config.properties'.format(verdi)
        intermediate = '{}/intermediate'.format(sparql_output)
        queries = '{}/queries'.format(args.output)

        # copy queries to be applied
        record_and_display_message(logger, 'Copying SPARQL queries to be applied.')
        call_system('mkdir {queries}'.format(queries=queries))
        call_system('cp /data/queries/AIDA_P3_TA1_*.rq {queries}'.format(task=args.task, queries=queries))

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
                python3.9 clean_sparql_output.py \
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
            python3.9 validate_responses.py \
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
            {sparql_clean_output} \
            {sparql_valid_output}'.format(python_scripts=python_scripts,
                                          log_file=log_file,
                                          log_specifications=log_specifications,
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
    # Align clusters and mentions, and filter SPARQL output
    #############################################################################################

    record_and_display_message(logger, 'Aligning clusters and mentions, and filtering SPARQL output.')

    log_file = '{logs_directory}/filter-responses.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3.9 filter_responses.py \
            --alpha {alpha} \
            --cache {cache} \
            --iou_thresholds {iou_thresholds} \
            --kgtk_api {kgtk_api} \
            --lock {lock} \
            --log {log_file} \
            --near_neighbor_similarity_value {near_neighbor_similarity_value} \
            --similarity_types {similarity_types} \
            --wait {wait} \
            {log_specifications} \
            {encoding_modality} \
            {coredocs} \
            {parent_children} \
            {sentence_boundaries} \
            {image_boundaries} \
            {keyframe_boundaries} \
            {video_boundaries} \
            {annotation_tagset} \
            {dwd_overlay} \
            {gold_valid_responses} \
            {run_id} \
            {sparql_valid_output} \
            {similarities} \
            {alignment} \
            {sparql_filtered_output}'.format(python_scripts=python_scripts,
                                          log_file=log_file,
                                          alpha=args.alpha,
                                          cache=cache,
                                          iou_thresholds=args.iou_thresholds,
                                          kgtk_api=args.kgtk_api,
                                          lock=args.lock,
                                          log_specifications=log_specifications,
                                          near_neighbor_similarity_value=args.near_neighbor_similarity_value,
                                          similarity_types='class,jc',
                                          wait=args.wait,
                                          encoding_modality=encoding_modality,
                                          coredocs=coredocs_xx,
                                          parent_children=parent_children,
                                          sentence_boundaries=sentence_boundaries,
                                          image_boundaries=image_boundaries,
                                          keyframe_boundaries=keyframe_boundaries,
                                          video_boundaries=video_boundaries,
                                          annotation_tagset=annotation_tagset,
                                          dwd_overlay=dwd_overlay,
                                          gold_valid_responses=gold_valid_responses,
                                          run_id=args.run,
                                          sparql_valid_output=sparql_valid_output,
                                          similarities=similarities,
                                          alignment=alignment,
                                          sparql_filtered_output=sparql_filtered_output)
    call_system(cmd)

    #############################################################################################
    # Generate scores
    #############################################################################################

    record_and_display_message(logger, 'Generating scores.')

    log_file = '{logs_directory}/score-responses.log'.format(logs_directory=logs_directory)
    cmd = 'cd {python_scripts} && \
            python3.9 score_submission.py \
            task1 \
            --log {log_file} \
            {log_specifications} \
            {encoding_modality} \
            {coredocs} \
            {parent_children} \
            {sentence_boundaries} \
            {image_boundaries} \
            {keyframe_boundaries} \
            {video_boundaries} \
            {gold_valid_responses} \
            {sparql_filtered_output} \
            {alignment} \
            {similarities} \
            {run_id} \
            {scores}'.format(python_scripts=python_scripts,
                                          log_file=log_file,
                                          log_specifications=log_specifications,
                                          encoding_modality=encoding_modality,
                                          coredocs=coredocs_xx,
                                          parent_children=parent_children,
                                          sentence_boundaries=sentence_boundaries,
                                          image_boundaries=image_boundaries,
                                          keyframe_boundaries=keyframe_boundaries,
                                          video_boundaries=video_boundaries,
                                          gold_valid_responses=gold_valid_responses,
                                          run_id=args.run,
                                          sparql_filtered_output=sparql_filtered_output,
                                          similarities=similarities,
                                          alignment=alignment,
                                          scores=scores)
    call_system(cmd)

    generate_results_file_and_exit(logger, logs_directory)

    record_and_display_message(logger, 'Done.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Apply SPARQL queries, validate responses, generate aggregate confidences, and scores.")
    parser.add_argument('-a', '--alpha', default=0.9, help='Specify the type similarity threshold (default: %(default)s)')
    parser.add_argument('-c', '--cache', default=None, help='Specify the qnode type similarity cache (default: %(default)s)')
    parser.add_argument('-i', '--input', default='/evaluate', help='Specify the input directory (default: %(default)s)')
    parser.add_argument('-I', '--iou_thresholds',
                        default='eng:image:0.9,eng:text:0.9,eng:video:0.9,rus:image:0.9,rus:text:0.9,rus:video:0.9,spa:image:0.9,spa:text:0.9,spa:video:0.9,ukr:image:0.9,ukr:text:0.9,ukr:video:0.9',
                        help='Specify comma-separted list of document, modality, and the respective iou threshold separated by colon (default: %(default)s)')
    parser.add_argument('-k', '--kgtk_api', default=None, help='Specify the URL of kgtk-similarity or leave it None (default: %(default)s)')
    parser.add_argument('-L', '--lock', default='/data/AUX-data/kgtk.lock', help='Specify the lock file (default: %(default)s)')
    parser.add_argument('-l', '--logs', default='logs', help='Specify the name of the logs directory to which different log files should be written (default: %(default)s)')
    parser.add_argument('-n', '--near_neighbor_similarity_value', default=0.9, help='Specify the similarity score to be used when the qnodes were declared to be near-neighbors (default: %(default)s)')
    parser.add_argument('-o', '--output', default='/score', help='Specify the input directory (default: %(default)s)')
    parser.add_argument('-r', '--run', default='system', help='Specify the run name (default: %(default)s)')
    parser.add_argument('-R', '--runtype', default='practice', help='Specify the run type (default: %(default)s)')
    parser.add_argument('-S', '--similarity_types', default='complex,transe,text,class,jc,topsim', help='Specify the comma-separated list of similarity types to be used by kgtk-similarity (default: %(default)s)')
    parser.add_argument('-s', '--spec', default='/scripts/log_specifications.txt', help='Specify the log specifications file (default: %(default)s)')
    parser.add_argument('-t', '--task', default='task1', help='Specify the task in order to apply relevant queries (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__,  help='Print version number and exit')
    parser.add_argument('-w', '--wait', type=int, default=10, help='Specify the seconds to wait before checking if the lock can be acquired (default: %(default)s)')
    args = parser.parse_args()
    main(args)
