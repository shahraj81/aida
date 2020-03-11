"""
AIDA main scoring script
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "15 January 2020"

from aida.assessments import Assessments
from aida.container import Container
from aida.core_documents import CoreDocuments
from aida.document_mappings import DocumentMappings
from aida.encodings import Encodings
from aida.file_handler import FileHandler
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.scores_manager import ScoresManager
from aida.logger import Logger
from aida.query_set import QuerySet
from aida.response_set import ResponseSet
from aida.text_boundaries import TextBoundaries

import argparse
import os
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_for_paths_existance(args):
    for path in [args.encodings_filename,
                 args.log_specifications_filename, 
                 args.core_documents_filename,
                 args.parent_children_filename,
                 args.sentence_boundaries_filename,
                 args.image_boundaries_filename,
                 args.keyframe_boundaries_filename,
                 args.queries_to_score_filename,
                 args.queries_xml_filename,
                 args.assessments_dir
                 ]:
        if not os.path.exists(path):
            print('Error: Path {} does not exist'.format(path))
            exit(ERROR_EXIT_CODE)

def score_submission(args):
    logger = Logger(args.log, args.log_specifications_filename, sys.argv)
    core_documents = CoreDocuments(logger, args.core_documents_filename)
    encodings = Encodings(logger, args.encodings_filename)
    document_mappings = DocumentMappings(logger, args.parent_children_filename, encodings, core_documents)
    text_boundaries = TextBoundaries(logger, args.sentence_boundaries_filename)
    image_boundaries = ImageBoundaries(logger, args.image_boundaries_filename)
    keyframe_boundaries = KeyFrameBoundaries(logger, args.keyframe_boundaries_filename)
    queries = QuerySet(logger, args.queries_xml_filename)
    queries_to_score = Container(logger)
    for entry in FileHandler(logger, args.queries_to_score_filename):
        queries_to_score.add(entry.get('query_id'), entry.get('query_id'))
    assessments = Assessments(logger, args.assessments_dir, queries.get('query_type'))
    response_set = ResponseSet(logger, queries, document_mappings, text_boundaries, image_boundaries, keyframe_boundaries, queries_to_score, args.runs_dir, args.runid)
    scores = ScoresManager(logger, args.runid, document_mappings, queries, response_set, assessments, queries_to_score, args.separator)
    print(scores)

# my $docid_mappings = DocumentIDsMappings->new($logger, $switches->get("docid_mappings"), CoreDocs->new($logger, $switches->get("coredocs")));
# my $text_document_boundaries = TextDocumentBoundaries->new($logger, $switches->get("sentence_boundaries"));
# my $images_boundingboxes = ImagesBoundingBoxes->new($logger, $switches->get("images_boundingboxes"));
# my $keyframes_boundingboxes = KeyFramesBoundingBoxes->new($logger, $switches->get("keyframes_boundingboxes"));
# my $queries = QuerySet->new($logger, $switches->get("queries_dtd"), $switches->get("queries_xml"));
# my $queries_to_score = Container->new($logger);
# map {$queries_to_score->add($_, $_->get("query_id"))}
#       FileHandler->new($logger, $switches->get("queries"))->get("ENTRIES")->toarray();
    
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Score the AIDA submission")
    # optional arguments
    parser.add_argument('-l', '--log', default='log.txt', 
                        help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, 
                        help='Print version number and exit')
    parser.add_argument('-s', '--strategy', default='strategy-1', choices=['strategy-1', 'strategy-2'],
                        help='Scoring strategy? (default: %(default)s)')
    parser.add_argument('-S', '--separator', default='pretty', choices=['pretty', 'tab', 'space'],
                        help='Column separator for scorer output? (default: %(default)s)')
    # positional arguments
    parser.add_argument('log_specifications_filename', type=str,
                        help='File containing error specifications')
    parser.add_argument('encodings_filename', type=str,
                        help='File containing list of encoding to modality mappings')
    parser.add_argument('core_documents_filename', type=str,
                        help='File containing list of core documents to be included in the pool')
    parser.add_argument('parent_children_filename', type=str,
                        help='DocumentID to DocumentElementID mappings file')
    parser.add_argument('sentence_boundaries_filename', type=str,
                        help='File containing sentence boundaries')
    parser.add_argument('image_boundaries_filename', type=str,
                        help='File containing image bounding boxes')
    parser.add_argument('keyframe_boundaries_filename', type=str,
                        help='File containing keyframe bounding boxes')
    parser.add_argument('queries_to_score_filename', type=str,
                        help='File containing queryids to be scored')
    parser.add_argument('queries_xml_filename', type=str,
                        help='XML file containing queries')
    parser.add_argument('assessments_dir', type=str,
                        help='Directory containing assessments package as received from LDC')
    parser.add_argument('runs_dir', type=str,
                        help='Directory containing runs')
    parser.add_argument('runid', type=str,
                        help='Run ID of the system being scored')
    # parse arguments    
    args = parser.parse_args()
    check_for_paths_existance(args)
    score_submission(args)