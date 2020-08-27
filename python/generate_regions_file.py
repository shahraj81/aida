"""
Generate regions file to be used by the AIDA evaluation docker.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "1.0.0.1"
__date__    = "25 August 2020"

from aida.file_handler import FileHandler
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.logger import Logger
from aida.container import Container
from aida.text_boundaries import TextBoundaries
from aida.video_boundaries import VideoBoundaries

import argparse
import os
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def check_paths(args):
    check_for_paths_existance([
                 args.log_specifications,
                 args.ontology_type_mappings,
                 args.sentence_boundaries,
                 args.image_boundaries,
                 args.keyframe_boundaries,
                 args.video_boundaries,
                 args.input,
                 ])
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

def multisort(xs, specs):
    for key, reverse in reversed(specs):
        xs.sort(key=lambda x: x[key], reverse=reverse)
    return xs

def get_line(output_object, columns):
    document_element_or_keyframe_id = output_object.get('keyframe_id') if output_object.get('keyframe_id') else output_object.get('document_element_id')
    output_object['document_element_or_keyframe_id'] = document_element_or_keyframe_id
    return '\t'.join([output_object[c] for c in columns])

def main(args):
    logger = Logger(args.log, args.log_specifications, sys.argv)

    type_mappings = Container(logger)
    for entry in FileHandler(logger, args.ontology_type_mappings):
        type_mappings.add(key=entry.get('full_type_ov'), value=entry.get('full_type'))

    text_boundaries = TextBoundaries(logger, args.sentence_boundaries)
    image_boundaries = ImageBoundaries(logger, args.image_boundaries)
    video_boundaries = VideoBoundaries(logger, args.video_boundaries)
    keyframe_boundaries = KeyFrameBoundaries(logger, args.keyframe_boundaries)
    document_boundaries = {
        'text': text_boundaries,
        'image': image_boundaries,
        'keyframe': keyframe_boundaries,
        'video': video_boundaries
        }

    output = []
    for entry in FileHandler(logger, args.input):
        document_id = entry.get('root_doc_id')
        document_element_id = entry.get('doc_element_id')
        modality = entry.get('media_type')
        type = entry.get('type')
        subtype = entry.get('subtype')
        subsubtype = entry.get('subsubtype')
        full_type = '{type}.{subtype}.{subsubtype}'.format(type=type, subtype=subtype, subsubtype=subsubtype)
        full_type_cleaned = full_type.replace('.unspecified', '')
        propercased_full_type = type_mappings.get(full_type_cleaned, None)
        span_string = entry.get('span')
        keyframe_id = None
        keyframe_num = 0
        if span_string == 'ENTIRE_DOCUMENT_ELEMENT':
            document_boundary = document_boundaries.get(modality).get(document_element_id)
            span_string = document_boundary.__str__()
        elif '-' in span_string:
            start, end = span_string.split('-')
            span_string = '({start},0)-({end},0)'.format(start=start, end=end)
        elif '_' in span_string:
            keyframe_id = span_string
            keyframe_num = span_string.split('_')[1]
            document_boundary = document_boundaries.get('keyframe').get(keyframe_id)
            span_string = document_boundary.__str__()
        else:
            span_string = None
        output_object = {
            'document_id': document_id,
            'document_element_id': document_element_id,
            'keyframe_id' : keyframe_id,
            'keyframe_num' : int(keyframe_num),
            'modality': modality,
            'region': span_string,
            'type': propercased_full_type,
            }
        output.append(output_object)

    printed = {}
    fh = open(args.output, 'w')
    header = ['document_id', 'document_element_or_keyframe_id', 'modality', 'region', 'type']
    fh.write('{}\n'.format('\t'.join(header)))
    for output_object in multisort(output, (('document_id', False), 
                                 ('modality', False), 
                                 ('document_element_id', False), 
                                 ('keyframe_num', False),
                                 ('region', False),
                                 ('type', False))):
        line = get_line(output_object, header)
        if line not in printed:
            fh.write('{}\n'.format(line))
            printed[line] = 1
    fh.close()
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate the regions file")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('-S', '--separator', default='pretty', choices=['pretty', 'tab', 'space'], help='Column separator for scorer output? (default: %(default)s)')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('ontology_type_mappings', type=str, help='File containing all the types in the ontology')
    parser.add_argument('sentence_boundaries', type=str, help='File containing sentence boundaries')
    parser.add_argument('image_boundaries', type=str, help='File containing image bounding boxes')
    parser.add_argument('keyframe_boundaries', type=str, help='File containing keyframe bounding boxes')
    parser.add_argument('video_boundaries', type=str, help='File containing length of videos')
    parser.add_argument('input', type=str, help='Specify the file to be converted (i.e. doc_regions_types_v*.tab).')
    parser.add_argument('output', type=str, help='Specify the file to which the output should be written.')
    args = parser.parse_args()
    check_paths(args)
    main(args)