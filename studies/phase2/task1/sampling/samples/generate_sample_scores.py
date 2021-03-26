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
                               args.runs,
                               args.samples,
                               args.aux_data])
    check_for_paths_non_existance([args.output])

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

def get_command(python_scripts, log_specifications, ldc_package_id, logs_directory,
                sample_size, sample_num, coredocs, aux_dir, gold_dir, runs_dir, runid, output_dir):
    sample_id = '{sample_size}-{sample_num}'.format(sample_size=sample_size,
                                                    sample_num=sample_num)
    sample_logs_dir = '{logs_directory}/{sample_id}'.format(logs_directory=logs_directory,
                                                            sample_id=sample_id)
    sample_output_dir = '{output_dir}/{sample_id}'.format(output_dir=output_dir,
                                                          sample_id=sample_id)
    for path in [sample_logs_dir, sample_output_dir]:
        if not os.path.exists(path):
            os.mkdir(path)
    os.mkdir('{sample_output_dir}/{runid}'.format(sample_output_dir=sample_output_dir,
                                                  runid=runid))
    log_file = '{sample_logs_dir}/{runid}.log'.format(sample_logs_dir=sample_logs_dir,
                                                      runid=runid)
    run_dir = '{runs_dir}/{runid}'.format(runs_dir=runs_dir,
                                          runid=runid)
    ontology_type_mappings  = '{}/AIDA_Annotation_Ontology_Phase2_V1.1_typemappings.tab'.format(aux_dir)
    slotname_mappings       = '{}/AIDA_Annotation_Ontology_Phase2_V1.1_slotnamemappings.tab'.format(aux_dir)
    encoding_modality       = '{}/encoding_modality.txt'.format(aux_dir)
    parent_children         = '{}/{}.parent_children.tsv'.format(aux_dir, ldc_package_id)
    sentence_boundaries     = '{}/{}.sentence_boundaries.txt'.format(aux_dir, ldc_package_id)
    image_boundaries        = '{}/{}.image_boundaries.txt'.format(aux_dir, ldc_package_id)
    keyframe_boundaries     = '{}/{}.keyframe_boundaries.txt'.format(aux_dir, ldc_package_id)
    video_boundaries        = '{}/{}.video_boundaries.txt'.format(aux_dir, ldc_package_id)
    annotated_regions       = '{}/{}.annotated_regions.txt'.format(aux_dir, ldc_package_id)
    sparql_filtered_output  = '{run_dir}/SPARQL-FILTERED-output'.format(run_dir=run_dir)
    alignment               = '{run_dir}/alignment'.format(run_dir=run_dir)
    similarities            = '{run_dir}/similarities'.format(run_dir=run_dir)
    scores                  = '{sample_output_dir}/{runid}/scores'.format(sample_output_dir=sample_output_dir,
                                                                          runid=runid)
    gold_filtered_responses = '{gold_dir}/SPARQL-FILTERED-output'.format(gold_dir=gold_dir)

    cmd = 'cd {python_scripts} && \
            python score_submission.py task1 \
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
            {runid} \
            {scores}'.format(python_scripts=python_scripts,
                             log_file=log_file,
                             log_specifications=log_specifications,
                             ontology_type_mappings = ontology_type_mappings,
                             slotname_mappings=slotname_mappings,
                             encoding_modality=encoding_modality,
                             coredocs=coredocs,
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
                             runid=runid,
                             scores=scores)
    return(cmd)

def call_system(cmd):
    cmd = ' '.join(cmd.split())
    print("running system command: '{}'".format(cmd))
    os.system(cmd)

def generate_sample_scores(args):
    os.mkdir(args.output)
    i = 1
    cmds = []
    for runid in os.listdir(args.runs):
        rundir = os.path.join(args.runs, runid)
        if not os.path.isdir(rundir): continue
        for sample in os.listdir(args.samples):
            sample_size, sample_num = sample.replace('coredocs-p','').split('.')[1].split('-')
            coredocs = os.path.join(args.samples, sample)
            cmd = get_command(args.python_scripts,
                              args.log_specifications,
                              args.ldc_package_id,
                              args.logs,
                              sample_size,
                              sample_num,
                              coredocs,
                              args.aux_data,
                              args.gold,
                              args.runs,
                              runid,
                              args.output)
            cmds.append(' '.join(cmd.split()))
    with Pool(16) as p:
        p.map(call_system, cmds)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate samples for the study.")
    parser.add_argument('-l', '--ldc_package_id', default='LDC2020R17', help='Specify the LDC Package ID to be used as a prefix of the output filenames (default: %(default)s).')
    parser.add_argument('python_scripts', type=str, help='Specify the directory containing scoring scripts.')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('logs', type=str, help='Specify a directory to which the log output should be written.')
    parser.add_argument('runs', type=str, help='Specify the directory containing scoring docker output corresponding to all runs.')
    parser.add_argument('samples', type=str, help='Specify the directory containing samples.')
    parser.add_argument('aux_data', type=str, help='Specify the AUX-data directory.')
    parser.add_argument('gold', type=str, help='Specify the gold data directory.')
    parser.add_argument('output', type=str, help='Specify a directory to which the output should be written.')
    args = parser.parse_args()
    check_path(args)
    generate_sample_scores(args)