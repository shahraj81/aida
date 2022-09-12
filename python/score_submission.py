"""
Main AIDA scoring script.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "1.0.0.1"
__date__    = "17 August 2020"

from aida.assessments import Assessments
from aida.cluster_alignment import ClusterAlignment
from aida.cluster_self_similarities import ClusterSelfSimilarities
from aida.core_documents import CoreDocuments
from aida.document_mappings import DocumentMappings
from aida.encodings import Encodings
from aida.file_handler import FileHandler
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.logger import Logger
from aida.object import Object
from aida.scores_manager import ScoresManager
from aida.response_set import ResponseSet
from aida.text_boundaries import TextBoundaries
from aida.type_similarities import TypeSimilarities
from aida.video_boundaries import VideoBoundaries

import argparse
import os
import re
import sys
import textwrap
import traceback

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

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

class Task1(Object):
    """
    Class representing Task1 scorer.
    """
    def __init__(self, log, runid, log_specifications, encodings, core_documents, parent_children, sentence_boundaries, image_boundaries, keyframe_boundaries, video_boundaries, gold, system, alignment, similarities, scores):
        check_for_paths_existance([
                 log_specifications,
                 encodings,
                 core_documents,
                 parent_children,
                 sentence_boundaries,
                 image_boundaries,
                 keyframe_boundaries,
                 video_boundaries,
                 gold,
                 system,
                 alignment,
                 similarities
                 ])
        check_for_paths_non_existance([scores])
        self.log_filename = log
        self.runid = runid
        self.log_specifications = log_specifications
        self.encodings = encodings
        self.core_documents = core_documents
        self.parent_children = parent_children
        self.sentence_boundaries = sentence_boundaries
        self.image_boundaries = image_boundaries
        self.keyframe_boundaries = keyframe_boundaries
        self.video_boundaries = video_boundaries
        self.gold = gold
        self.system = system
        self.alignment = alignment
        self.similarities = similarities
        self.scores = scores
        self.logger = Logger(self.get('log_filename'),
                        self.get('log_specifications'),
                        sys.argv)

    def __call__(self):
        logger = self.get('logger')
        document_mappings = DocumentMappings(logger,
                                             self.get('parent_children'),
                                             Encodings(logger, self.get('encodings')),
                                             CoreDocuments(logger, self.get('core_documents')))
        text_boundaries = TextBoundaries(logger, self.get('sentence_boundaries'))
        image_boundaries = ImageBoundaries(logger, self.get('image_boundaries'))
        video_boundaries = VideoBoundaries(logger, self.get('video_boundaries'))
        keyframe_boundaries = KeyFrameBoundaries(logger, self.get('keyframe_boundaries'))
        document_boundaries = {
            'text': text_boundaries,
            'image': image_boundaries,
            'keyframe': keyframe_boundaries,
            'video': video_boundaries
            }
        gold_responses = ResponseSet(logger, document_mappings, document_boundaries, self.get('gold'), 'gold', 'task1')
        system_responses = ResponseSet(logger, document_mappings, document_boundaries, self.get('system'), self.get('runid'), 'task1')
        cluster_alignment = ClusterAlignment(logger, self.get('alignment'))
        type_similarities = TypeSimilarities(logger, self.get('similarities'))
        cluster_self_similarities = ClusterSelfSimilarities(logger, self.get('similarities'))
        arguments = {
            'run_id': self.get('runid'),
            'gold_responses': gold_responses,
            'system_responses': system_responses,
            'cluster_alignment': cluster_alignment,
            'cluster_self_similarities': cluster_self_similarities,
            'type_similarities': type_similarities,
            }
        scores = ScoresManager(logger, 'task1', arguments)
        scores.print_scores(self.get('scores'))
        logger.record_event('DEFAULT_INFO', 'done.')
        exit(ALLOK_EXIT_CODE)

    @classmethod
    def add_arguments(myclass, parser):
        parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
        parser.add_argument('log_specifications', type=str, help='File containing error specifications')
        parser.add_argument('encodings', type=str, help='File containing list of encoding to modality mappings')
        parser.add_argument('core_documents', type=str, help='File containing list of core documents')
        parser.add_argument('parent_children', type=str, help='DocumentID to DocumentElementID mappings file')
        parser.add_argument('sentence_boundaries', type=str, help='File containing sentence boundaries')
        parser.add_argument('image_boundaries', type=str, help='File containing image bounding boxes')
        parser.add_argument('keyframe_boundaries', type=str, help='File containing keyframe bounding boxes')
        parser.add_argument('video_boundaries', type=str, help='File containing length of videos')
        parser.add_argument('gold', type=str, help='Directory containing gold information.')
        parser.add_argument('system', type=str, help='Directory containing system information.')
        parser.add_argument('alignment', type=str, help='Directory containing alignment information.')
        parser.add_argument('similarities', type=str, help='Directory containing similarity information.')
        parser.add_argument('runid', type=str, help='Run ID of the system being scored')
        parser.add_argument('scores', type=str, help='Specify a directory to which the scores should be written.')
        parser.set_defaults(myclass=myclass)
        return parser

class Task2(Object):
    """
    Class representing Task2 scorer.
    """
    def __init__(self, log, runid, cutoff, normalize, weighted, log_specifications, encodings, core_documents, parent_children, sentence_boundaries, image_boundaries, keyframe_boundaries, video_boundaries, queries_to_score, assessments, responses, scores):
        check_for_paths_existance([
                 log_specifications,
                 encodings,
                 core_documents,
                 parent_children,
                 sentence_boundaries,
                 image_boundaries,
                 keyframe_boundaries,
                 video_boundaries,
                 queries_to_score,
                 assessments,
                 responses,
                 '{}/SPARQL-VALID-output'.format(responses)
                 ])
        check_for_paths_non_existance([scores])
        self.log_filename = log
        self.runid = runid
        self.cutoff = cutoff
        self.normalize = normalize
        self.weighted = weighted
        self.log_specifications = log_specifications
        self.encodings = encodings
        self.core_documents = core_documents
        self.parent_children = parent_children
        self.sentence_boundaries = sentence_boundaries
        self.image_boundaries = image_boundaries
        self.keyframe_boundaries = keyframe_boundaries
        self.video_boundaries = video_boundaries
        self.queries_to_score = queries_to_score
        self.assessments = assessments
        self.responses = '{}/SPARQL-VALID-output'.format(responses)
        self.scores = scores
        self.logger = Logger(self.get('log_filename'),
                        self.get('log_specifications'),
                        sys.argv)

    def __call__(self):
        logger = self.get('logger')
        document_mappings = DocumentMappings(logger,
                                             self.get('parent_children'),
                                             Encodings(logger, self.get('encodings')),
                                             CoreDocuments(logger, self.get('core_documents')))
        text_boundaries = TextBoundaries(logger, self.get('sentence_boundaries'))
        image_boundaries = ImageBoundaries(logger, self.get('image_boundaries'))
        video_boundaries = VideoBoundaries(logger, self.get('video_boundaries'))
        keyframe_boundaries = KeyFrameBoundaries(logger, self.get('keyframe_boundaries'))
        document_boundaries = {
            'text': text_boundaries,
            'image': image_boundaries,
            'keyframe': keyframe_boundaries,
            'video': video_boundaries
            }
        queries_to_score = {}
        for entry in FileHandler(logger, self.get('queries_to_score')):
            queries_to_score[entry.get('query_id')] = entry

        assessments = Assessments(logger, 'task2', queries_to_score, self.get('assessments'))
        responses = ResponseSet(logger, document_mappings, document_boundaries, self.get('responses'), self.get('runid'), task='task2')
        arguments = {
            'run_id': self.get('runid'),
            'cutoff': self.get('cutoff'),
            'normalize': self.get('normalize'),
            'weighted': self.get('weighted'),
            'assessments': assessments,
            'responses': responses,
            'queries_to_score': queries_to_score
            }
        scores = ScoresManager(logger, 'task2', arguments)
        scores.print_scores(self.get('scores'))
        exit(ALLOK_EXIT_CODE)

    @classmethod
    def add_arguments(myclass, parser):
        parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
        parser.add_argument('-C', '--cutoff', action='store_true', help='Apply cutoff?')
        parser.add_argument('-N', '--normalize', action='store_true', help='Normalize confidences?')
        parser.add_argument('-W', '--weighted', action='store_true', help='Use weighted Value for AP computation?')
        parser.add_argument('log_specifications', type=str, help='File containing error specifications')
        parser.add_argument('encodings', type=str, help='File containing list of encoding-to-modality mappings')
        parser.add_argument('core_documents', type=str, help='File containing list of core documents')
        parser.add_argument('parent_children', type=str, help='File containing parent-to-child document ID mappings')
        parser.add_argument('sentence_boundaries', type=str, help='File containing sentence boundaries')
        parser.add_argument('image_boundaries', type=str, help='File containing image bounding boxes')
        parser.add_argument('keyframe_boundaries', type=str, help='File containing keyframe bounding boxes')
        parser.add_argument('video_boundaries', type=str, help='File containing length of videos')
        parser.add_argument('queries_to_score', type=str, help='File containing list of queryids to be scored')
        parser.add_argument('assessments', type=str, help='Directory containing assessments')
        parser.add_argument('responses', type=str, help='Directory containing output of AIDA evaluation docker')
        parser.add_argument('runid', type=str, help='ID of the system being scored')
        parser.add_argument('scores', type=str, help='Directory to which the scores should be written')
        parser.set_defaults(myclass=myclass)
        return parser

class Task3(Object):
    """
    Class representing Task3 scorer.
    """
    def __init__(self, log, runid, log_specifications, encodings, core_documents, parent_children, sentence_boundaries, image_boundaries, keyframe_boundaries, video_boundaries, queries, queries_to_score, query_claim_frames, claim_mappings, assessments, responses, assessments_wc, scores):
        check_for_paths_existance([
                 log_specifications,
                 encodings,
                 core_documents,
                 parent_children,
                 sentence_boundaries,
                 image_boundaries,
                 keyframe_boundaries,
                 video_boundaries,
                 queries,
                 queries_to_score,
                 query_claim_frames,
                 claim_mappings,
                 assessments,
                 responses
                 ])
        check_for_paths_non_existance([assessments_wc, scores])
        self.log_filename = log
        self.runid = runid
        self.log_specifications = log_specifications
        self.encodings = encodings
        self.core_documents = core_documents
        self.parent_children = parent_children
        self.sentence_boundaries = sentence_boundaries
        self.image_boundaries = image_boundaries
        self.keyframe_boundaries = keyframe_boundaries
        self.video_boundaries = video_boundaries
        self.queries = queries
        self.queries_to_score = queries_to_score
        self.query_claim_frames = query_claim_frames
        self.claim_mappings = claim_mappings
        self.assessments = assessments
        self.responses = responses
        self.assessments_wc = assessments_wc
        self.scores = scores
        self.logger = Logger(self.get('log_filename'),
                        self.get('log_specifications'),
                        sys.argv)

    def __call__(self):
        logger = self.get('logger')
        queries_to_score = {}
        for entry in FileHandler(logger, self.get('queries_to_score')):
            queries_to_score[entry.get('query_id')] = entry

        assessments_package=self.get('assessments')
        assessments_dir = self.get('assessments_wc')
        claims_dir = os.path.join(assessments_dir, 'claims')
        os.makedirs(claims_dir)
        # copy system claims as is
        source_dir = os.path.join(assessments_package, 'data', 'TA3', 'system_claims')
        command = 'cp {source}/* {destination}/'.format(source=source_dir, destination=claims_dir)
        os.system(command)
        # copy ldc claims and mark every field correct
        source_dir = os.path.join(assessments_package, 'data', 'TA3', 'ldc_claims')
        if os.path.exists(source_dir) and os.path.isdir(source_dir):
            for filename in os.listdir(source_dir):
                if filename.endswith('-outer-claim.tab'):
                    with open(os.path.join(claims_dir, filename), 'w') as corrected_claims_output:
                        filehandler = FileHandler(logger, os.path.join(source_dir, filename))
                        corrected_claims_output.write('{}\n'.format(filehandler.get('header').get('line')))
                        for entry in filehandler:
                            if entry.get('correctness') == 'NIL':
                                corrected_value = 'Informative' if entry.get('fieldname') == 'informativenessAssessment' else 'Correct'
                                entry.set('correctness', corrected_value)
                                line = [entry.get(fieldname) for fieldname in entry.get('header').get('columns')]
                                entry.set('line', '{}\n'.format('\t'.join(line)))
                            corrected_claims_output.write(entry.get('line'))
                else:
                    command = 'cp {source}/{filename} {destination}/'.format(filename=filename, source=source_dir, destination=claims_dir)
                    os.system(command)
        command = 'cp {source}/cross_claim_relations.tab {destination}/'.format(source=os.path.join(assessments_package, 'data', 'TA3'), destination=assessments_dir)
        os.system(command)
        claim_relations = os.path.join(assessments_dir, 'cross_claim_relations.tab')

        assessments = Assessments(logger, 'task3', queries_to_score, claims_dir, claim_mappings=self.get('claim_mappings'), claim_relations=claim_relations)
        arguments = {
            'run_id': self.get('runid'),
            'assessments': assessments,
            'responses_dir': self.get('responses'),
            'queries_to_score': queries_to_score,
            }
        scores = ScoresManager(logger, 'task3', arguments)
        scores.print_scores(self.get('scores'))
        exit(ALLOK_EXIT_CODE)

    @classmethod
    def add_arguments(myclass, parser):
        parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
        parser.add_argument('log_specifications', type=str, help='File containing error specifications')
        parser.add_argument('encodings', type=str, help='File containing list of encoding-to-modality mappings')
        parser.add_argument('core_documents', type=str, help='File containing list of core documents')
        parser.add_argument('parent_children', type=str, help='File containing parent-to-child document ID mappings')
        parser.add_argument('sentence_boundaries', type=str, help='File containing sentence boundaries')
        parser.add_argument('image_boundaries', type=str, help='File containing image bounding boxes')
        parser.add_argument('keyframe_boundaries', type=str, help='File containing keyframe bounding boxes')
        parser.add_argument('video_boundaries', type=str, help='File containing length of videos')
        parser.add_argument('queries', type=str, help='Specify the directory containing task3 user queries')
        parser.add_argument('queries_to_score', type=str, help='File containing list of queryids to be scored')
        parser.add_argument('query_claim_frames', type=str, help='Directory containing output of NIST evaluation docker when applied to query claim frames represented as a Condition5 run')
        parser.add_argument('claim_mappings', type=str, help='File containing claim mappings (claim-mappings.tab)')
        parser.add_argument('assessments', type=str, help='Directory containing the assessments package as recieved from LDC')
        parser.add_argument('responses', type=str, help='Directory containing output of AIDA evaluation docker')
        parser.add_argument('runid', type=str, help='ID of the system being scored')
        parser.add_argument('assessments_wc', type=str, help='Directory to which the working copy of the assessments package should be written')
        parser.add_argument('scores', type=str, help='Directory to which the scores should be written')
        parser.set_defaults(myclass=myclass)
        return parser

myclasses = [
    Task1,
    Task2,
    Task3
    ]

def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(prog='score_submission',
                                description='Score an AIDA submission')
    subparser = parser.add_subparsers()
    subparsers = {}
    for myclass in myclasses:
        hyphened_name = re.sub('([A-Z])', r'-\1', myclass.__name__).lstrip('-').lower()
        help_text = myclass.__doc__.split('\n')[0]
        desc = textwrap.dedent(myclass.__doc__.rstrip())

        class_subparser = subparser.add_parser(hyphened_name,
                            help=help_text,
                            description=desc,
                            formatter_class=argparse.RawDescriptionHelpFormatter)
        myclass.add_arguments(class_subparser)
        subparsers[myclass] = class_subparser

    namespace = vars(parser.parse_args(args))
    try:
        myclass = namespace.pop('myclass')
    except KeyError:
        parser.print_help()
        return
    try:
        obj = myclass(**namespace)
    except ValueError as e:
        subparsers[myclass].error(str(e) + "\n" + traceback.format_exc())
    result = obj()
    if result is not None:
        print(result)

if __name__ == '__main__':
    main()