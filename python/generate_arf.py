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
from aida.ta3_queryset import TA3QuerySet
from aida.text_boundaries import TextBoundaries
from aida.image_boundaries import ImageBoundaries
from aida.keyframe_boundaries import KeyFrameBoundaries
from aida.video_boundaries import VideoBoundaries

import argparse
import os
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

class OutputLine(Object):
    def __init__(self, claim_id, component_type, component_number, field_name, field_value, default_assessment_value):
        self.claim_id = claim_id
        self.component_type = component_type
        self.component_number = component_number
        self.field_name = field_name
        self.field_value = field_value
        self.default_assessment_value = default_assessment_value

    def __str__(self):
        values = [str(self.get(f)) for f in ['claim_id', 'component_type', 'component_number', 'field_name', 'field_value', 'default_assessment_value']]
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
        non_assessed_fields = [
            'claim_topic',
            'claim_subtopic',
            'claim_description',
            'document_id'
            ]
        subfield_names = {
            'claim_epistemic_status': ['polarity', 'strength']
            }
        entry = self.get('entry')
        lines = []
        for field_name in fields:
            field_name_output = fields.get(field_name)
            field_value = entry.get(field_name)
            default_assessment_value = '--' if field_name in non_assessed_fields else 'NIL'
            subfield_name = ['value'] if field_name not in subfield_names else subfield_names.get(field_name)
            for sn in subfield_name:
                line = OutputLine(self.get('entry').get('claim_id'), field_name_output, 1, sn, field_value, default_assessment_value)
                lines.append(line.__str__())
        return '\n'.join(lines)

class ClaimComponents(Object):
    def __init__(self, logger, max_qnode_types, lenient, claim_components):
        super().__init__(logger)
        self.max_qnode_types = max_qnode_types
        self.lenient = lenient
        self.entries = claim_components

    def __str__(self):
        logger = self.get('logger')
        component_numbers = {}
        lines = []
        processed = set()
        for entry in self.get('entries'):
            claim_component_key = entry.get('claim_component_key')
            if claim_component_key not in processed:
                processed.add(claim_component_key)
            else:
                continue
            component_type = entry.get('claim_component_type')
            if component_type not in component_numbers:
                component_numbers[component_type] = 1
            else:
                component_numbers[component_type] += 1
            lines.append(ClaimComponent(logger, self.get('max_qnode_types'), self.get('lenient'), entry, component_numbers[component_type]).__str__())
            lines.append(InformativenessAssessment(logger, entry.get('claim_id'), component_type, component_numbers[component_type]).__str__())
            lines.append(OverallAssessment(logger, entry.get('claim_id'), component_type, component_numbers[component_type]).__str__())
        return '\n'.join(lines)

class ClaimComponent(Object):
    def __init__(self, logger, max_qnode_types, lenient, claim_component, claim_component_number):
        super().__init__(logger)
        self.max_qnode_types = max_qnode_types
        self.lenient = lenient
        self.entry = claim_component
        self.claim_component_number = claim_component_number

    def get_claim_component_name(self):
        return self.get('entry').get('claim_component_name')

    def get_claim_component_qnode_id(self):
        return self.get('entry').get('claim_component_qnode_id')

    def get_claim_component_qnode_type(self):
        claim_component_qnode_types_provided = self.get('entry').get('claim_component_qnode_types')
        i = self.get('max_qnode_types')
        if len(claim_component_qnode_types_provided) <= i:
            return ','.join(claim_component_qnode_types_provided)
        self.record_event('UNEXPECTED_NUM_CLAIM_COMPONENT_QNODE_TYPES', self.get('entry').get('claim_component_key'), len(claim_component_qnode_types_provided), i, self.get('entry').get('where'))
        claim_component_qnode_types_selected = set()
        for claim_component_qnode_type in sorted(self.get('entry').get('claim_component_qnode_types')):
            if i:
                claim_component_qnode_types_selected.add(claim_component_qnode_type)
                i -= 1
        return ','.join(sorted(claim_component_qnode_types_selected))

    def __str__(self):
        claim_id = self.get('entry').get('claim_id')
        claim_component_type = self.get('entry').get('claim_component_type')
        claim_component_number = self.get('claim_component_number')
        fields = {
            'claim_component_name': 'name',
            'claim_component_qnode_id': 'qnode_id',
            'claim_component_qnode_type': 'qnode_type',
            }
        tuples = set()
        for field_name in fields:
            field_name_output = fields.get(field_name)
            field_value = self.get(field_name)
            if field_name == 'claim_component_qnode_type':
                for fv in sorted(field_value.split(',')):
                    tuples.add((field_name_output, fv))
            else:
                tuples.add((field_name_output, field_value))
            if field_name == 'claim_component_qnode_id' and self.get('lenient') == True:
                tuples.add((fields.get('claim_component_qnode_type'), field_value))
        lines = []
        for (field_name_output, field_value) in sorted(tuples):
            line = OutputLine(claim_id, claim_component_type, claim_component_number, field_name_output, field_value, 'NIL')
            lines.append(line.__str__())
        return '\n'.join(lines)

class ClaimTime(Object):
    def __init__(self, logger, claim_time):
        super().__init__(logger)
        self.entry = claim_time

    def get_range_str(self):
        date_range = {}
        date_types = ['start_after', 'start_before', 'end_after', 'end_before']
        for date_type in date_types:
            field_name_day = '{}_day'.format(date_type)
            field_name_month = '{}_month'.format(date_type)
            field_name_year = '{}_year'.format(date_type)
            date_str = '{}-{}-{}'.format(self.get('entry').get(field_name_year),
                                         self.get('entry').get(field_name_month),
                                         self.get('entry').get(field_name_day))
            date_str = date_str.replace('"','')
            date_range[date_type] = date_str
        range_str = '({},{})-({},{})'.format(date_range.get('start_after'),
                                             date_range.get('start_before'),
                                             date_range.get('end_after'),
                                             date_range.get('end_before'))
        if range_str == '(0001-01-01,9999-12-31)-(0001-01-01,9999-12-31)':
            return
        return range_str

    def __str__(self):
        if self.get('entry') is None:
            return
        range_str = self.get('range_str')
        if range_str is None:
            return
        line = OutputLine(self.get('entry').get('claim_id'), 'date', 1, 'range', range_str, 'NIL')
        return line.__str__()

class ClaimKEs(Object):
    def __init__(self, logger, claim, nextEdgeNum):
        super().__init__(logger)
        self.claim = claim
        self.nextEdgeNum = nextEdgeNum
        self.lines = None
        self.generate()

    def get_fields(self):
        return [
            'ClaimID',
            'JustificationNum',
            'EdgeID',
            'EdgeLabel',
            'IsEdgeNegated',
            'EvtRelMetatype',
            'EvtRelType',
            'EvtRelClusterID',
            'IsEvtRelNegated',
            'ObjMetatype',
            'ObjectType',
            'ObjClusterID',
            'IsObjNegated',
            'ObjectHandle',
            'DocID',
            'SubjectJustification',
            'PredicateJustification',
            'ArgumentJustification'
            ]

    def get_header(self):
        return '\t'.join(self.get('fields'))

    def get_JustificationNum(self, entry):
        edgeNum = self.get('nextEdgeNum')
        self.set('nextEdgeNum', edgeNum + 1)
        return edgeNum

    def get_line(self, entry):
        field_specs = self.get('fieldspecs')
        line = {}
        for field_name, entry_key in field_specs.items():
            if entry_key is not None:
                value = entry.get(entry_key)
            else:
                value = str(self.get(field_name, entry))
            line[field_name] = value
        return '\t'.join([line.get(f) for f in self.get('fields')])

class ClaimNonTemporalKEs(ClaimKEs):
    def __init__(self, logger, claim, nextEdgeNum):
        super().__init__(logger, claim, nextEdgeNum)

    def get_EdgeID(self, entry):
        return '{subject}::{predicate}::{object}'.format(
            subject=entry.get('subject_cluster_id'),
            predicate=entry.get('predicate'),
            object=entry.get('object_cluster_id'))

    def get_fieldspecs(self):
        return {
            'ClaimID': 'claim_id',
            'JustificationNum': None,
            'EdgeID': None,
            'EdgeLabel': 'predicate',
            'IsEdgeNegated': 'is_assertion_negated',
            'EvtRelMetatype': 'subject_cluster_member_metatype',
            'EvtRelType': 'subject_type',
            'EvtRelClusterID': 'subject_cluster_id',
            'IsEvtRelNegated': 'is_subject_cluster_member_negated',
            'ObjMetatype': 'object_cluster_member_metatype',
            'ObjectType': 'object_type',
            'ObjClusterID': 'object_cluster_id',
            'IsObjNegated': 'is_object_cluster_member_negated',
            'ObjectHandle': 'object_cluster_handle',
            'DocID': 'document_id',
            'SubjectJustification': 'subject_informative_justification_span_text',
            'PredicateJustification': 'predicate_justification_spans_text',
            'ArgumentJustification': 'object_informative_justification_span_text'
            }

    def generate(self):
        lines = []
        lines.append(self.get('header'))
        for entry in self.get('claim').get('claim_edge_assertions'):
            lines.append(self.get('line', entry))
        self.set('lines', lines)

    def __str__(self):
        return '\n'.join(self.get('lines'))

class ClaimTemporalKEs(ClaimKEs):
    def __init__(self, logger, claim, nextEdgeNum):
        self.line_keys = set()
        super().__init__(logger, claim, nextEdgeNum)

    def get_corresponding_time_assertion(self, entry):
        subject_cluster_id = entry.get('subject_cluster_id')
        claim = entry.get('claim')
        for entry in claim.get('claim_edge_subject_times'):
            if entry.get('subject_cluster_id') == subject_cluster_id:
                return entry

    def get_predicate(self, entry):
        return 'Time'

    def get_EdgeID(self, entry):
        return '{subject}::{predicate}::{object}'.format(
            subject=entry.get('subject_cluster_id'),
            predicate=self.get('predicate', entry),
            object=self.get('ObjClusterID', entry))

    def get_EdgeLabel(self, entry):
        return self.get('predicate', entry)

    def get_IsEdgeNegated(self, entry):
        return 'NotNegated'

    def get_IsEvtRelNegated(self, entry):
        return 'NotNegated'

    def get_ObjMetatype(self, entry):
        return 'Time'

    def get_ObjectType(self, entry):
        return 'TMP'

    def get_ObjClusterID(self, entry):
        return 'TIME'

    def get_IsObjNegated(self, entry):
        return 'NotNegated'

    def get_ObjectHandle(self, entry):
        time_assertion_entry = self.get('corresponding_time_assertion', entry)
        date_range = {}
        date_types = ['start_after', 'start_before', 'end_after', 'end_before']
        for date_type in date_types:
            field_name_day = '{}_day'.format(date_type)
            field_name_month = '{}_month'.format(date_type)
            field_name_year = '{}_year'.format(date_type)
            date_str = '{}-{}-{}'.format(time_assertion_entry.get(field_name_year),
                                         time_assertion_entry.get(field_name_month),
                                         time_assertion_entry.get(field_name_day))
            date_str = date_str.replace('"','')
            date_range[date_type] = date_str
        range_str = '{};{};{};{}'.format(date_range.get('start_after'),
                                             date_range.get('start_before'),
                                             date_range.get('end_after'),
                                             date_range.get('end_before'))
        return range_str

    def get_SubjectJustification(self, entry):
        return 'NULL'

    def get_PredicateJustification(self, entry):
        return 'NULL'

    def get_ArgumentJustification(self, entry):
        return 'NULL'

    def get_fieldspecs(self):
        return {
            'ClaimID': 'claim_id',
            'JustificationNum': None,
            'EdgeID': None,
            'EdgeLabel': None,
            'IsEdgeNegated': None,
            'EvtRelMetatype': 'subject_cluster_member_metatype',
            'EvtRelType': 'subject_type',
            'EvtRelClusterID': 'subject_cluster_id',
            'IsEvtRelNegated': None,
            'ObjMetatype': None,
            'ObjectType': None,
            'ObjClusterID': None,
            'IsObjNegated': None,
            'ObjectHandle': None,
            'DocID': 'document_id',
            'SubjectJustification': None,
            'PredicateJustification': None,
            'ArgumentJustification': None
            }

    def get_line(self, entry):
        field_specs = self.get('fieldspecs')
        line = {}
        for field_name, entry_key in field_specs.items():
            if entry_key is not None:
                value = entry.get(entry_key)
            else:
                value = str(self.get(field_name, entry))
            line[field_name] = value

        if line.get('ObjectHandle') == '0001-01-01;9999-12-31;0001-01-01;9999-12-31':
            return

        line_str = '\t'.join([line.get(f) for f in self.get('fields')])
        line_key_str = '\t'.join([line.get(f) for f in self.get('fields') if f != 'JustificationNum'])

        if line_key_str in self.get('line_keys'):
            self.set('nextEdgeNum', self.get('nextEdgeNum') - 1)
            return None
        self.get('line_keys').add(line_key_str)
        return line_str

    def generate(self):
        lines = []
        # lines.append(self.get('header'))
        for entry in self.get('claim').get('claim_edge_assertions'):
            line = self.get('line', entry)
            if line is not None:
                lines.append(line)
        self.set('lines', lines)

    def __str__(self):
        return '\n'.join(self.get('lines'))

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
        missing = ['01-01-0001', '31-12-9999', '0001-01-01', '9999-12-31']
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
            date_str = '{}-{}-{}'.format(entry.get(field_name_year),
                                         entry.get(field_name_month),
                                         entry.get(field_name_day))
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
        line = OutputLine(self.get('claim_id'), self.get('component_type'), self.get('number'), 'informativenessAssessment', 'value', 'NIL')
        return line.__str__()

class OverallAssessment(Object):
    def __init__(self, logger, claim_id, component_type, number):
        super().__init__(logger)
        self.claim_id = claim_id
        self.component_type = component_type
        self.number = number

    def __str__(self):
        line = OutputLine(self.get('claim_id'), self.get('component_type'), self.get('number'), 'overallAssessment', 'value', 'NIL')
        return line.__str__()

class AssessorReadableFormat(Object):
    def __init__(self, logger, responses, max_qnode_types, lenient):
        super().__init__(logger)
        self.responses = responses
        self.max_qnode_types = max_qnode_types
        self.lenient = lenient

    def write_output(self, output_dir):
        def get_claim_output_dir(output_dir, claim):
            claim_condition = claim.get('claim_condition')
            claim_query_topic_or_claim_frame_id = claim.get('claim_query_topic_or_claim_frame_id')
            claim_output_dir = os.path.join(output_dir, claim_condition, claim_query_topic_or_claim_frame_id)
            return claim_output_dir
        os.mkdir(output_dir)
        logger = self.get('logger')
        header = ['claim_id', 'component_type', 'id', 'fieldname', 'value', 'correctness']
        for claim_uid in self.get('responses').get('claims'):
            claim = self.get('responses').get('claims').get(claim_uid)
            outer_claim = OuterClaim(logger, claim.get('outer_claim')).__str__()
            claim_components = ClaimComponents(logger, self.get('max_qnode_types'), self.get('lenient'), claim.get('claim_components')).__str__()
            claim_time = ClaimTime(logger, claim.get('claim_time')).__str__()
            claim_output_dir = get_claim_output_dir(output_dir, claim)
            os.makedirs(claim_output_dir, exist_ok=True)
            output_filename = os.path.join(claim_output_dir, '{}-outer-claim.tab'.format(claim.get('claim_id')))
            output_fh = open(output_filename, 'w', encoding='utf-8')
            output_str = '\t'.join(header)
            output_str = '{}\n{}'.format(output_str, outer_claim)
            if claim_time is not None:
                output_str = '{}\n{}'.format(output_str, claim_time)
            output_str = '{}\n{}'.format(output_str, claim_components)
            output_fh.write(output_str)
            output_fh.close()
        for claim_uid in self.get('responses').get('claims'):
            frames = EventOrRelationFrames(logger, claim_uid)
            claim = self.get('responses').get('claims').get(claim_uid)
            for edge_assertion in claim.get('claim_edge_assertions'):
                frames.update(edge_assertion)
            for subject_time in claim.get('claim_edge_subject_times'):
                frames.update(subject_time)
            claim_output_dir = get_claim_output_dir(output_dir, claim)
            os.makedirs(claim_output_dir, exist_ok=True)
            output_filename = os.path.join(claim_output_dir, '{}-readable-kes.txt'.format(claim.get('claim_id')))
            output_fh = open(output_filename, 'w', encoding='utf-8')
            output_fh.write(frames.__str__())
            output_fh.close()
        for claim_uid in self.get('responses').get('claims'):
            claim = self.get('responses').get('claims').get(claim_uid)
            claim_nontemoral_kes = ClaimNonTemporalKEs(logger, claim, 1)
            nextEdgeNum = claim_nontemoral_kes.get('nextEdgeNum')
            claim_temoral_kes = ClaimTemporalKEs(logger, claim, nextEdgeNum)
            claim_output_dir = get_claim_output_dir(output_dir, claim)
            os.makedirs(claim_output_dir, exist_ok=True)
            output_filename = os.path.join(claim_output_dir, '{}-raw-kes.tab'.format(claim.get('claim_id')))
            output_fh = open(output_filename, 'w', encoding='utf-8')
            output_fh.write(claim_nontemoral_kes.__str__())
            output_fh.write('\n')
            output_fh.write(claim_temoral_kes.__str__())
            output_fh.close()

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

    queries = TA3QuerySet(logger, args.queries) if args.queries else None
    responses = ResponseSet(logger, document_mappings, document_boundaries, args.input, args.runid, 'task3', queries=queries)
    arf = AssessorReadableFormat(logger, responses, args.max_qnode_types, args.lenient)
    arf.write_output(args.output)
    num_warnings, num_errors = logger.get_stats()
    closing_message = 'ARF generation finished (warnings:{}, errors:{})'.format(num_warnings, num_errors)
    logger.record_event('DEFAULT_INFO', closing_message)
    print(closing_message)
    if num_errors > 0:
        exit(ERROR_EXIT_CODE)
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate claims in assessor readable format.")
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-n', '--lenient', action='store_true', default=True, help='Consider identity-qnode as type-qnode? (default: %(default)s)')
    parser.add_argument('-q', '--queries', help='Specify the directory containing task3 user queries')
    parser.add_argument('-t', '--max_qnode_types', default=5, help='Specify the maximum number of qnode types allowed in output (default: %(default)s)')
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