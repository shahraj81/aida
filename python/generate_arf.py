"""
AIDA main script for generating claims in assessor readable format.
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "13 January 2022"

from aida.logger import Logger
from aida.object import Object
from aida.response_set import ResponseSet
from aida.encodings import Encodings
from aida.core_documents import CoreDocuments
from aida.document_mappings import DocumentMappings
from aida.text_boundaries import TextBoundaries
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.video_boundaries import VideoBoundaries

import argparse
import os
import shutil
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

class OutputLine(Object):
    def __init__(self, claim_id, component_type, component_number, field_name, field_value):
        self.claim_id = claim_id
        self.component_type = component_type
        self.component_number = component_number
        self.field_name = field_name
        self.field_value = field_value

    def __str__(self):
        values = [str(self.get(f)) for f in ['claim_id', 'component_type', 'component_number', 'field_name', 'field_value']]
        values.extend(['NIL'])
        return '\t'.join(values)

class OuterClaim(Object):
    def __init__(self, logger, outer_claim):
        super().__init__(logger)
        self.entry = outer_claim

    def __str__(self):
        fields = {
            'claim_topic': 'claimTopic',
            'claim_subtopic': 'claimSubtopic',
            'claim_description': 'claimDescription',
            'claim_template': 'claimTemplate',
            'document_id': 'claimDocument',
            'claim_epistemic_status': 'claimEpistemic',
            'claim_sentiment_status': 'claimSentiment',
            }
        entry = self.get('entry')
        lines = []
        for field_name in fields:
            field_name_output = fields.get(field_name)
            field_value = entry.get(field_name)
            line = OutputLine(self.get('entry').get('claim_id'), field_name_output, 1, 'value', field_value)
            lines.append(line.__str__())
        return '\n'.join(lines)

class ClaimComponents(Object):
    def __init__(self, logger, claim_components):
        super().__init__(logger)
        self.entries = claim_components

    def __str__(self):
        logger = self.get('logger')
        component_numbers = {}
        lines = []
        for entry in self.get('entries'):
            component_type = entry.get('claim_component_type')
            if component_type not in component_numbers:
                component_numbers[component_type] = 1
            else:
                component_numbers[component_type] += 1
            line = ClaimComponent(logger, entry, component_numbers[component_type]).__str__()
            # lines.append(SummaryAssessment(logger, entry.get('claim_id'), component_type, component_numbers[component_type]).__str__())
            lines.append(InformativenessAssessment(logger, entry.get('claim_id'), component_type, component_numbers[component_type]).__str__())
            lines.append(line)
        return '\n'.join(lines)

class ClaimComponent(Object):
    def __init__(self, logger, claim_component, claim_component_number):
        super().__init__(logger)
        self.entry = claim_component
        self.claim_component_number = claim_component_number

    def __str__(self):
        claim_id = self.get('entry').get('claim_id')
        claim_component_type = self.get('entry').get('claim_component_type')
        claim_component_number = self.get('claim_component_number')
        fields = {
            'claim_component_name': 'name',
            'claim_component_qnode_id': 'qnode_id',
            'claim_component_qnode_type': 'qnode_type',
            }
        lines = []
        for field_name in fields:
            field_name_output = fields.get(field_name)
            field_value = self.get('entry').get(field_name)
            line = OutputLine(claim_id, claim_component_type, claim_component_number, field_name_output, field_value)
            lines.append(line.__str__())
        return '\n'.join(lines)

class ClaimTime(Object):
    def __init__(self, logger, claim_time):
        super().__init__(logger)
        self.entry = claim_time

    def __str__(self):
        date_range = {}
        date_types = ['start_after', 'start_before', 'end_after', 'end_before']
        for date_type in date_types:
            field_name_day = '{}_day'.format(date_type)
            field_name_month = '{}_month'.format(date_type)
            field_name_year = '{}_year'.format(date_type)
            date_str = '{}-{}-{}'.format(self.get('entry').get(field_name_day),
                                         self.get('entry').get(field_name_month),
                                         self.get('entry').get(field_name_year))
            date_str = date_str.replace('"','')
            date_range[date_type] = date_str
        range_str = '({},{})-({},{})'.format(date_range.get('start_after'),
                                             date_range.get('start_before'),
                                             date_range.get('end_after'),
                                             date_range.get('end_before'))
        line = OutputLine(self.get('entry').get('claim_id'), 'date', 1, 'range', range_str)
        return line.__str__()

class EventOrRelationRoleFiller(Object):
    def __init__(self, logger, object_metatype, object_id, object_type, object_handle):
        super().__init__(logger)
        self.object_metatype = object_metatype
        self.object_id = object_id
        self.object_type = object_type
        self.object_handle = object_handle

    def __str__(self):
        elements = [self.get(f) for f in ['object_metatype', 'object_type', 'object_handle', 'object_id']]
        return '\t'.join(elements)

class EventOrRelationFrame(Object):
    def __init__(self, logger, claim_id, uid, event_or_relation_metatype, event_or_relation_id, event_or_relation_type):
        super().__init__(logger)
        self.claim_id = claim_id
        self.uid = uid
        self.event_or_relation_metatype = event_or_relation_metatype
        self.event_or_relation_id = event_or_relation_id
        self.event_or_relation_type = event_or_relation_type
        self.date_range = None
        self.fillers = {}

    def get_date(self, date_range, key):
        missing = ['01-01-0001', '31-12-9999']
        retVal = 'n/a'
        if key in date_range:
            value = date_range.get(key)
            if value not in missing:
                retVal = value
        return retVal

    def get_date_range_str(self):
        fields = {
            'T1': 'start_after',
            'T2': 'start_before',
            'T3': 'end_after',
            'T4': 'end_before',
            }
        lines = []
        date_range = self.get('date_range')
        for field_name, key in fields.items():
            desc = key.replace('_', ' on or ')
            line = '\tTime {field_name} ({desc}): {date}'.format(field_name=field_name,
                                                     desc=desc,
                                                     date=self.get('date', date_range, key))
            lines.append(line)
        return '\n'.join(lines)

    def add(self, *args, **kwargs):
        key = args[0]
        if key is None:
            self.get('logger').record_event('KEY_IS_NONE', self.get('code_location'))
        method_name = "add_{}".format(key)
        method = self.get_method(method_name)
        if method is not None:
            args = args[1:]
            method(*args, **kwargs)
            return self
        else:
            self.record_event('METHOD_NOT_FOUND', method_name)

    def add_date_range(self, date_range):
        if self.get('date_range') is not None:
            self.record_event('MULTIPLE_DATES')
        self.set('date_range', date_range)

    def add_filler(self, predicate, filler):
        fillers = self.get('fillers')
        if predicate not in fillers:
            fillers[predicate] = []
        fillers.get(predicate).append(filler)

    def __str__(self):
        event_or_relation_metatype = self.get('event_or_relation_metatype')
        event_or_relation_id = self.get('event_or_relation_id')
        event_or_relation_type = self.get('event_or_relation_type')
        uid = self.get('uid')
        line1 = '{metatype}:{id}'.format(metatype=event_or_relation_metatype,
                                         id=event_or_relation_id)
        line2 = event_or_relation_type
        line3 = '\tUID: {uid}'.format(uid=uid)
        lines = [line1, line2, line3]
        lines.append(self.get('date_range_str'))
        fillers = self.get('fillers')
        argnum = 0
        for predicate, filler_list in fillers.items():
            for filler in filler_list:
                argnum += 1
                arg = 'arg{}'.format(argnum)
                elements = ['', arg, predicate, filler.__str__()]
                lines.append('\t'.join(elements))
        return '\n'.join(lines)

class EventOrRelationFrames(Object):
    def __init__(self, logger, claim_id):
        super().__init__(logger)
        self.claim_id = claim_id
        self.frames = {}

    def get_frame(self, uid, event_or_relation_metatype, event_or_relation_id, event_or_relation_type):
        frames = self.get('frames')
        if uid not in frames:
            frames[uid] = EventOrRelationFrame(self.get('logger'), self.get('claim_id'), uid,
                                               event_or_relation_metatype, event_or_relation_id, event_or_relation_type)
        return frames.get(uid)

    def update(self, entry):
        if entry.get('schema').get('name') == 'AIDA_PHASE3_TASK3_TM_RESPONSE':
            self.update_time(entry)
        elif entry.get('schema').get('name') == 'AIDA_PHASE3_TASK3_GR_RESPONSE':
            self.update_rolefiller(entry)

    def update_time(self, entry):
        date_range = {}
        date_types = ['start_after', 'start_before', 'end_after', 'end_before']
        for date_type in date_types:
            field_name_day = '{}_day'.format(date_type)
            field_name_month = '{}_month'.format(date_type)
            field_name_year = '{}_year'.format(date_type)
            date_str = '{}-{}-{}'.format(entry.get(field_name_day),
                                         entry.get(field_name_month),
                                         entry.get(field_name_year))
            date_str = date_str.replace('"','')
            date_range[date_type] = date_str
        subject_cluster_id = entry.get('subject_cluster_id')
        for frame in self.get('frames').values():
            if frame.get('event_or_relation_id') == subject_cluster_id:
                frame.add('date_range', date_range)

    def update_rolefiller(self, entry):
        event_or_relation_metatype = entry.get('subject_cluster_member_metatype')
        event_or_relation_id = entry.get('subject_cluster_id')
        event_or_relation_type = entry.get('subject_type')
        uid = '{metatype}:{id}:{type}'.format(metatype=event_or_relation_metatype,
                                              id=event_or_relation_id,
                                              type=event_or_relation_type)
        predicate = entry.get('predicate')
        object_metatype = entry.get('object_cluster_member_metatype')
        object_id = entry.get('object_cluster_id')
        object_type = entry.get('object_type')
        object_handle = entry.get('object_cluster_handle')

        filler = EventOrRelationRoleFiller(self.get('logger'), object_metatype, object_id, object_type, object_handle)
        frame = self.get('frame', uid, event_or_relation_metatype, event_or_relation_id, event_or_relation_type)
        frame.add('filler', predicate, filler)

    def __str__(self):
        lines = []
        frames = self.get('frames')
        for frame in frames.values():
            lines.append(frame.__str__())
        return '\n\n'.join(lines)

class InformativenessAssessment(Object):
    def __init__(self, logger, claim_id, component_type, number):
        super().__init__(logger)
        self.claim_id = claim_id
        self.component_type = component_type
        self.number = number

    def __str__(self):
        line = OutputLine(self.get('claim_id'), self.get('component_type'), self.get('number'), 'informativenessAssessment', 'value')
        return line.__str__()

class SummaryAssessment(Object):
    def __init__(self, logger, claim_id, component_type, number):
        super().__init__(logger)
        self.claim_id = claim_id
        self.component_type = component_type
        self.number = number

    def __str__(self):
        line = OutputLine(self.get('claim_id'), self.get('component_type'), self.get('number'), 'summaryAssessment', 'value')
        return line.__str__()

class AssessorReadableFormat(Object):
    def __init__(self, logger, responses):
        super().__init__(logger)
        self.responses = responses

    def write_output(self, output_dir):
        os.mkdir(output_dir)
        logger = self.get('logger')
        header = ['claim_id', 'component_type', 'id', 'fieldname', 'value', 'correctness']
        for claim_id in self.get('responses').get('claims'):
            claim = self.get('responses').get('claims').get(claim_id)
            outer_claim = OuterClaim(logger, claim.get('outer_claim')).__str__()
            claim_components = ClaimComponents(logger, claim.get('claim_components')).__str__()
            claim_time = ClaimTime(logger, claim.get('claim_time')).__str__()
            output_filename = os.path.join(output_dir, '{}-outer-claim.tab'.format(claim_id))
            output_fh = open(output_filename, 'w', encoding='utf-8')
            output_str = '\t'.join(header)
            output_str = '{}\n{}'.format(output_str, outer_claim)
            output_str = '{}\n{}'.format(output_str, claim_time)
            output_str = '{}\n{}'.format(output_str, claim_components)
            output_fh.write(output_str)
            output_fh.close()
        for claim_id in self.get('responses').get('claims'):
            frames = EventOrRelationFrames(logger, claim_id)
            claim = self.get('responses').get('claims').get(claim_id)
            graph_responses_file = None
            for edge_assertion in claim.get('claim_edge_assertions'):
                if graph_responses_file is None:
                    graph_responses_file = edge_assertion.get('filename')
                frames.update(edge_assertion)
            for subject_time in claim.get('claim_edge_subject_times'):
                frames.update(subject_time)
            output_filename = os.path.join(output_dir, '{}-readable-kes.txt'.format(claim_id))
            output_fh = open(output_filename, 'w', encoding='utf-8')
            output_fh.write(frames.__str__())
            output_fh.close()

            if graph_responses_file is not None:
                output_filename = os.path.join(output_dir, '{}-raw-kes.tab'.format(claim_id))
                shutil.copy(graph_responses_file, output_filename)

def check_path(args):
    check_for_paths_existance([args.log_specifications,
                               args.encodings,
                               args.core_documents,
                               args.parent_children,
                               args.sentence_boundaries,
                               args.image_boundaries,
                               args.keyframe_boundaries,
                               args.video_boundaries,
                               args.input])
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

def validate_responses(args):
    logger = Logger(args.log, args.log_specifications, sys.argv)

    logger.record_event('DEFAULT_INFO', 'validation started')
    document_mappings = DocumentMappings(logger,
                                         args.parent_children,
                                         Encodings(logger, args.encodings),
                                         CoreDocuments(logger, args.core_documents))
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

    responses = ResponseSet(logger, document_mappings, document_boundaries, args.input, args.runid, 'task3')
    arf = AssessorReadableFormat(logger, responses)
    arf.write_output(args.output)
    num_warnings, num_errors = logger.get_stats()
    closing_message = 'validation finished (warnings:{}, errors:{})'.format(num_warnings, num_errors)
    logger.record_event('DEFAULT_INFO', closing_message)
    print(closing_message)
    if num_errors > 0:
        exit(ERROR_EXIT_CODE)
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate claims in assessor readable format.")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('encodings', type=str, help='File containing list of encoding to modality mappings')
    parser.add_argument('core_documents', type=str, help='File containing list of core documents to be included in the pool')
    parser.add_argument('parent_children', type=str, help='DocumentID to DocumentElementID mappings file')
    parser.add_argument('sentence_boundaries', type=str, help='File containing sentence boundaries')
    parser.add_argument('image_boundaries', type=str, help='File containing image bounding boxes')
    parser.add_argument('keyframe_boundaries', type=str, help='File containing keyframe bounding boxes')
    parser.add_argument('video_boundaries', type=str, help='File containing length of videos')
    parser.add_argument('runid', type=str, help='Run ID of the system being scored')
    parser.add_argument('input', type=str, help='Directory containing valid responses.')
    parser.add_argument('output', type=str, help='Directory where assessor readable format is to be written.')
    args = parser.parse_args()
    check_path(args)
    validate_responses(args)