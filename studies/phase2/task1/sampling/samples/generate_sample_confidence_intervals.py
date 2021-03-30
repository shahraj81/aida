"""
AIDA main script generating samples for the study.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "26 March 2021"

from multiprocessing import Pool

import argparse
import os

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_path(args):
    check_for_paths_existance([args.python_scripts,
                               args.logs,
                               args.samples])
    check_for_paths_non_existance([])

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

def get_metric_classes_specs():

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
        # TypeMetricV1
        #
          TypeMetricV1-scores.txt        TypeMetricV1_F1                       Language:ALL,Metatype:ALL      F1

          TypeMetricV1-scores.txt        TypeMetricV1_Events_F1                Language:ALL,Metatype:Event    F1
          TypeMetricV1-scores.txt        TypeMetricV1_Entities_F1              Language:ALL,Metatype:Entity   F1

          TypeMetricV1-scores.txt        TypeMetricV1_ENG_F1                   Language:ENG,Metatype:ALL      F1
          TypeMetricV1-scores.txt        TypeMetricV1_ENG_Events_F1            Language:ENG,Metatype:Event    F1
          TypeMetricV1-scores.txt        TypeMetricV1_ENG_Entities_F1          Language:ENG,Metatype:Entity   F1

          TypeMetricV1-scores.txt        TypeMetricV1_RUS_F1                   Language:RUS,Metatype:ALL      F1
          TypeMetricV1-scores.txt        TypeMetricV1_RUS_Events_F1            Language:RUS,Metatype:Event    F1
          TypeMetricV1-scores.txt        TypeMetricV1_RUS_Entities_F1          Language:RUS,Metatype:Entity   F1

          TypeMetricV1-scores.txt        TypeMetricV1_SPA_F1                   Language:SPA,Metatype:ALL      F1
          TypeMetricV1-scores.txt        TypeMetricV1_SPA_Events_F1            Language:SPA,Metatype:Event    F1
          TypeMetricV1-scores.txt        TypeMetricV1_SPA_Entities_F1          Language:SPA,Metatype:Entity   F1

        # ---
        # TypeMetricV2
        #
          TypeMetricV2-scores.txt        TypeMetricV2_MAP                       Language:ALL,Metatype:ALL      AvgPrec

          TypeMetricV2-scores.txt        TypeMetricV2_Events_MAP                Language:ALL,Metatype:Event    AvgPrec
          TypeMetricV2-scores.txt        TypeMetricV2_Entities_MAP              Language:ALL,Metatype:Entity   AvgPrec

          TypeMetricV2-scores.txt        TypeMetricV2_ENG_MAP                   Language:ENG,Metatype:ALL      AvgPrec
          TypeMetricV2-scores.txt        TypeMetricV2_ENG_Events_MAP            Language:ENG,Metatype:Event    AvgPrec
          TypeMetricV2-scores.txt        TypeMetricV2_ENG_Entities_MAP          Language:ENG,Metatype:Entity   AvgPrec

          TypeMetricV2-scores.txt        TypeMetricV2_RUS_MAP                   Language:RUS,Metatype:ALL      AvgPrec
          TypeMetricV2-scores.txt        TypeMetricV2_RUS_Events_MAP            Language:RUS,Metatype:Event    AvgPrec
          TypeMetricV2-scores.txt        TypeMetricV2_RUS_Entities_MAP          Language:RUS,Metatype:Entity   AvgPrec

          TypeMetricV2-scores.txt        TypeMetricV2_SPA_MAP                   Language:SPA,Metatype:ALL      AvgPrec
          TypeMetricV2-scores.txt        TypeMetricV2_SPA_Events_MAP            Language:SPA,Metatype:Event    AvgPrec
          TypeMetricV2-scores.txt        TypeMetricV2_SPA_Entities_MAP          Language:SPA,Metatype:Entity   AvgPrec

        # ---
        # TypeMetricV3
        #
          TypeMetricV3-scores.txt        TypeMetricV3_MAP                       Language:ALL,Metatype:ALL      AvgPrec

          TypeMetricV3-scores.txt        TypeMetricV3_Events_MAP                Language:ALL,Metatype:Event    AvgPrec
          TypeMetricV3-scores.txt        TypeMetricV3_Entities_MAP              Language:ALL,Metatype:Entity   AvgPrec

          TypeMetricV3-scores.txt        TypeMetricV3_ENG_MAP                   Language:ENG,Metatype:ALL      AvgPrec
          TypeMetricV3-scores.txt        TypeMetricV3_ENG_Events_MAP            Language:ENG,Metatype:Event    AvgPrec
          TypeMetricV3-scores.txt        TypeMetricV3_ENG_Entities_MAP          Language:ENG,Metatype:Entity   AvgPrec

          TypeMetricV3-scores.txt        TypeMetricV3_RUS_MAP                   Language:RUS,Metatype:ALL      AvgPrec
          TypeMetricV3-scores.txt        TypeMetricV3_RUS_Events_MAP            Language:RUS,Metatype:Event    AvgPrec
          TypeMetricV3-scores.txt        TypeMetricV3_RUS_Entities_MAP          Language:RUS,Metatype:Entity   AvgPrec

          TypeMetricV3-scores.txt        TypeMetricV3_SPA_MAP                   Language:SPA,Metatype:ALL      AvgPrec
          TypeMetricV3-scores.txt        TypeMetricV3_SPA_Events_MAP            Language:SPA,Metatype:Event    AvgPrec
          TypeMetricV3-scores.txt        TypeMetricV3_SPA_Entities_MAP          Language:SPA,Metatype:Entity   AvgPrec

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
    return metric_classes_specs

def get_commands(python_scripts, log_specifications, logs_directory, sample_id, sample_dir):
    cmds = []
    for run_id in os.listdir(sample_dir):
        log_file = os.path.join(logs_directory, sample_id, '{}-ci.log'.format(run_id))
        scores = os.path.join(sample_dir, run_id, 'scores')
        metric_classes_specs = get_metric_classes_specs()
        added = {}
        for line in metric_classes_specs.split('\n'):
            line = line.strip()
            if line == '': continue
            if line.startswith('#'): continue
            filename, metricname, column_value_pairs, score_columnname = line.split()
            scorer_name = filename.split('-')[0]
            if scorer_name in added: continue
            cmd = 'cd {python_scripts} && \
                    python generate_confidence_intervals.py \
                    --log {log_file} \
                    {log_specifications} \
                    {primary_key} \
                    {score_columnname} \
                    {aggregate} \
                    {run_id} \
                    {input} \
                    {pretty_output} \
                    {tab_output}'.format(python_scripts=python_scripts,
                                        log_file=log_file,
                                        log_specifications=log_specifications,
                                        primary_key='RunID,Language,Metatype',
                                        score_columnname=score_columnname,
                                        aggregate='DocID:Summary',
                                        run_id='RunID',
                                        input='{}/{}-scores.tab'.format(scores, scorer_name),
                                        pretty_output='{}/{}-ci.txt'.format(scores, scorer_name),
                                        tab_output='{}/{}-ci.tab'.format(scores, scorer_name))
                    
            cmds.append(' '.join(cmd.split()))
            added[scorer_name] = 1
    return(cmds)

def call_system(cmd):
    cmd = ' '.join(cmd.split())
    print("running system command: '{}'".format(cmd))
    os.system(cmd)

def generate_sample_confidence_intervals(args):
    cmds = []
    for sample_id in sorted(os.listdir(args.samples), reverse=True):
        sample_dir = os.path.join(args.samples, sample_id)
        cmd = get_commands(args.python_scripts, args.log_specifications, args.logs, sample_id, sample_dir)
        cmds.extend(cmd)
    with Pool(16) as p:
        p.map(call_system, cmds)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate confidence intervals corresponding to sample scores for the study.")
    parser.add_argument('-l', '--ldc_package_id', default='LDC2020R17', help='Specify the LDC Package ID to be used as a prefix of the output filenames (default: %(default)s).')
    parser.add_argument('python_scripts', type=str, help='Specify the directory containing scoring scripts.')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('logs', type=str, help='Specify a directory to which the log output should be written.')
    parser.add_argument('samples', type=str, help='Specify the directory containing sample scores. This is where the output should be written.')
    args = parser.parse_args()
    check_path(args)
    generate_sample_confidence_intervals(args)