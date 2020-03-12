"""
AIDA AIF generator
"""

__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "7 February 2019"


#############################################################################
# TODOs:
#############################################################################
# TODO # 1: add a switch to allow/disallow reading picture/sound channel
#    - based time frame spans
#
# STATUS: Pending
#    - handled via annotations
#    - switch not currently being read via command-line
# ---------------------------------------------------------------------------
# TODO # 2: add LDCTime
#
# STATUS: Complete
#    - added, but patch needed for correctly printing year
#    - patch applied to correctly print year
# ---------------------------------------------------------------------------
# TODO # 3: For reference KB IDs 690791 and 80000032, Next century's output 
#     contains different number of informative justifications, why? Likely a bug.
#     Are these not confusable nodes? Yes
#
# lehigh:aida-python skr1$ grep 690791 -A 1 example-data/example-m18-kb/LDC_2.LDC_2.ttl | grep informativeJustification
#         aida:informativeJustification  _:b1190 , _:b1616 , _:b227 , _:b3347 , _:b393 , _:b3992 , _:b4158 , _:b4177 , _:b453 , _:b4838 , _:b5391 , _:b5850 , _:b593 , _:b6109 , _:b6382 , _:b7304 , _:b8285 , _:b914 , _:b9493 , _:b9629 ;
# lehigh:aida-python skr1$ grep 80000032 -A 1 example-data/example-m18-kb/LDC_2.LDC_2.ttl | grep informativeJustification
#         aida:informativeJustification  _:b163 , _:b1692 , _:b1977 , _:b1987 , _:b2078 , _:b2095 , _:b2290 , _:b2345 , _:b2501 , _:b2756 , _:b3014 , _:b33 , _:b3764 , _:b378 , _:b3891 , _:b4060 , _:b5639 , _:b6160 , _:b6429 , _:b674 , _:b6760 , _:b6832 , _:b6916 , _:b7028 , _:b729 , _:b7422 , _:b7545 , _:b7560 , _:b7613 , _:b7641 , _:b7674 , _:b7739 , _:b8531 , _:b858 , _:b8733 , _:b8781 , _:b8920 , _:b9189 , _:b9541 , _:b9774 , _:b9905 ;
#
# STATUS: This issue does not appear in the NIST output
# ---------------------------------------------------------------------------
# TODO # 4: Following entity is not a member of any cluster, why?
#     ldc:EMIC00160R8.002266 a aida:Entity ;
#
# STATUS: Complete
# ---------------------------------------------------------------------------
# TODO # 5: Add only one mention to compound justification.
#
# STATUS: Complete
#     - handled via calling a different function
#     - original function is left unchanged
# ---------------------------------------------------------------------------
# TODO # 6: Equivalent cluster in LDC's confusable node list not to be split
#
# STATUS: Ignored as this should not appear in LDC's annotation data in M36, 
# (decided by Hoa)
# ---------------------------------------------------------------------------
# TODO # 7: Change the Picture/Sound channel justification to VideoJustification
# with an optional attribute, say, 'channel' with three values 'picture', 'sound'
# or 'both'. Also add a switch to turn on/off generation of the optional attribute.
#
# STATUS: Pending
#     - Justifications updated
#     - Switch pending
# ---------------------------------------------------------------------------
# TODO # 8: Tests on informative justifications are failing
#
# STATUS: Pending

from aida.object import Object
from aida.utility import get_md5_from_string
from rdflib import Graph
from re import compile

SYSTEM_NAME = 'ldc:LDCModelGenerator'

def patch(serialized_output):
    print('--patching output')
    patched_output = serialized_output.replace('-01-01"^^xsd:gYear', '"^^xsd:gYear')
    return patched_output

def generate_cluster_membership_triples(node):
    cluster_membership_triples = []
    for mention_id in node.get('mentions'):
        cluster_membership_md5 = get_md5_from_string('{node_name}:{mention_id}'.format(node_name = node.get('name'),
                                                                                     mention_id = mention_id))
        triples = """\
            _:bcm-{cluster_membership_md5} a aida:ClusterMembership .
            _:bcm-{cluster_membership_md5} aida:cluster ldc:cluster-{node_name} .
            _:bcm-{cluster_membership_md5} aida:clusterMember ldc:{mention_id} .
            _:bcm-{cluster_membership_md5} aida:confidence _:bcm-{cluster_membership_md5}-confidence .
            _:bcm-{cluster_membership_md5}-confidence a aida:Confidence .
            _:bcm-{cluster_membership_md5}-confidence aida:confidenceValue '1.0'^^xsd:double .
            _:bcm-{cluster_membership_md5}-confidence aida:system {system} .
            _:bcm-{cluster_membership_md5} aida:system {system} .
        """.format(cluster_membership_md5 = cluster_membership_md5,
                   node_name = node.get('name'),
                   mention_id = mention_id,
                   system = SYSTEM_NAME)
        cluster_membership_triples.append(triples)
    return '\n'.join(cluster_membership_triples)

def generate_cluster_triples(reference_kb_id, node):
    node_ids = []
    node_id_or_node_ids = node.get('id')
    for node_id in node_id_or_node_ids.split('|'):
        if not node_id.startswith('NIL'):
            node_ids.append(node_id)
    link_assertion_triples = []
    for node_id in node_ids:
        triples = """\
            ldc:cluster-{node_name} aida:link _:blinkassertion{node_id} .
            _:blinkassertion{node_id} a aida:LinkAssertion .
            _:blinkassertion{node_id} aida:linkTarget "{reference_kb_id}:{node_id}" .
            _:blinkassertion{node_id} aida:system {system} .
            _:blinkassertion{node_id} aida:confidence _:blinkassertion{node_id}-confidence .
            _:blinkassertion{node_id}-confidence a aida:Confidence .
            _:blinkassertion{node_id}-confidence aida:confidenceValue '1.0'^^xsd:double .
            _:blinkassertion{node_id}-confidence aida:system {system} .
        """.format(node_name = node.get('name'),
                   reference_kb_id = reference_kb_id,
                   node_id = node_id,
                   system = SYSTEM_NAME
                   )
        link_assertion_triples.append(triples)
    
    informative_justification_spans = node.get('informative_justification_spans')
    informative_justification_triples = []
    for span in informative_justification_spans.values():
        triple = 'ldc:cluster-{node_name} aida:informativeJustification _:b{span_md5} .'.format(node_name=node.get('name'),
                                                                                               span_md5=span.get('md5'))
        informative_justification_triples.append(triple)
    triples = """\
        ldc:cluster-{node_name} a aida:SameAsCluster .
        ldc:cluster-{node_name} aida:prototype _:b{prototype_span_md5} .
        {informative_justification_triples}
        {link_assertion_triples}
    """.format(node_name = node.get('name'),
               informative_justification_triples = '\n'.join(informative_justification_triples),
               link_assertion_triples = '\n'.join(link_assertion_triples),
               prototype_span_md5 = node.get('prototype').get('md5'),
               system = SYSTEM_NAME,
               node_id = node.get('id'),
               reference_kb_id = reference_kb_id)
    return triples

def generate_ere_object_triples(reference_kb_id, ere_object):
    def get_ldc_time_triples(logger, date_iri, date_string, date_type, where):
        type_map = {
                'starton' : 'ON',
                'endon' : 'ON',
                'startbefore' : 'BEFORE',
                'endbefore' : 'BEFORE',
                'endunk' : 'UNKNOWN',
                'endafter' : 'AFTER',
                'startafter' : 'AFTER',
                'startunk' : 'UNKNOWN'
            }
        ldc_time_triples = {}
        ldc_time_triples['day'] = ''
        ldc_time_triples['month'] = ''
        ldc_time_triples['year'] = ''
        ldc_time_triples['type'] = ''
        
        if date_type is not None:
            ldc_time_triples['type'] = '{date_iri} aida:timeType "{type}" .'.format(date_iri = date_iri,
                                                                                    type = type_map[date_type])

        if date_string is not None and date_string != 'EMPTY_NA':
            pattern = compile('^(....)-(..)-(..)$')
            match = pattern.match(date_string)
            if match:
                year = match.group(1)
                month = match.group(2)
                day = match.group(3)
                if year != 'xxxx':
                    ldc_time_triples['year'] = '{date_iri} aida:year "{year}"^^xsd:gYear .'.format(date_iri = date_iri,
                                                                                                   year = year)
                if month != 'xx':
                    ldc_time_triples['month'] = '{date_iri} aida:month "--{month}"^^xsd:gMonth .'.format(date_iri = date_iri,
                                                                                                       month = month)
                if day != 'xx':
                    ldc_time_triples['day'] = '{date_iri} aida:day "---{day}"^^xsd:gDay .'.format(date_iri = date_iri,
                                                                                               day = day)
            else:
                logger.record_event('UNEXPECTED_DATE_FORMAT', date_string, where)
        return ldc_time_triples
    
    logger = ere_object.get('logger')
    where = ere_object.get('where')
    ere_type = ere_object.get('node_metatype').capitalize()
    
    # generate ldc time assertion triples
    ldc_time_assertion_triples = ''
    if ere_type in ['Event', 'Relation']:        
        # ldc start time triples
        ldc_start_time_blank_node_iri = '_:bldctime{ere_object_id}-start'.format(ere_object_id = ere_object.get('id'))
        ldc_start_time_triples = get_ldc_time_triples(logger,
                                                      ldc_start_time_blank_node_iri,
                                                      ere_object.get('entry').get('start_date'),
                                                      ere_object.get('entry').get('start_date_type'),
                                                      where)
        
        ldc_start_time_triples = """\
            _:bldctime{ere_object_id} aida:start {ldc_start_time_blank_node_iri} .
            {ldc_start_time_blank_node_iri} a aida:LDCTimeComponent .
            {ldc_start_time_day_triples}
            {ldc_start_time_month_triples}
            {ldc_start_time_year_triples}
            {ldc_start_time_type_triples}
        """.format(ere_object_id = ere_object.get('id'),
                   ldc_start_time_blank_node_iri = ldc_start_time_blank_node_iri,
                   ldc_start_time_day_triples = ldc_start_time_triples['day'],
                   ldc_start_time_month_triples = ldc_start_time_triples['month'],
                   ldc_start_time_year_triples = ldc_start_time_triples['year'],
                   ldc_start_time_type_triples = ldc_start_time_triples['type'])

        # ldc end time triples
        ldc_end_time_blank_node_iri = '_:bldctime{ere_object_id}-end'.format(ere_object_id = ere_object.get('id'))
        ldc_end_time_triples = get_ldc_time_triples(logger,
                                                    ldc_end_time_blank_node_iri,
                                                    ere_object.get('entry').get('end_date'),
                                                    ere_object.get('entry').get('end_date_type'),
                                                    where)
        
        ldc_end_time_triples = """\
            _:bldctime{ere_object_id} aida:end {ldc_end_time_blank_node_iri} .
            {ldc_end_time_blank_node_iri} a aida:LDCTimeComponent .
            {ldc_end_time_day_triples}
            {ldc_end_time_month_triples}
            {ldc_end_time_year_triples}
            {ldc_end_time_type_triples}
        """.format(ere_object_id = ere_object.get('id'),
                   ldc_end_time_blank_node_iri = ldc_end_time_blank_node_iri,
                   ldc_end_time_day_triples = ldc_end_time_triples['day'],
                   ldc_end_time_month_triples = ldc_end_time_triples['month'],
                   ldc_end_time_year_triples = ldc_end_time_triples['year'],
                   ldc_end_time_type_triples = ldc_end_time_triples['type'])

        ldc_time_assertion_triples = """\
            ldc:{ere_object_id} aida:ldcTime _:bldctime{ere_object_id} .
            _:bldctime{ere_object_id} a aida:LDCTime .
            _:bldctime{ere_object_id} aida:system {system} .
            {ldc_start_time_triples}
            {ldc_end_time_triples}
        """.format(ere_object_id = ere_object.get('id'),
                   ldc_start_time_triples = ldc_start_time_triples,
                   ldc_end_time_triples = ldc_end_time_triples,
                   system = SYSTEM_NAME)
    
    
    # generate link assertion triples
    has_name_triple = ''
    if ere_type == 'Entity':
        text_string = ere_object.get('entry').get('text_string')
        if len(text_string) < 256 and ere_object.get('entry').get('level') == 'nam':
            has_name_triple = 'ldc:{ere_object_id} aida:hasName "{text_string}" .'.format(ere_object_id=ere_object.get('id'),
                                                                                      text_string=text_string.replace('"', '\\"'))
    node_ids = []
    for node_id_or_node_ids in ere_object.get('nodes'):
        for node_id in node_id_or_node_ids.split('|'):
            if not node_id.startswith('NIL'):
                node_ids.append(node_id)
    link_assertion_triples = []
    for node_id in node_ids:
        triples = """\
            ldc:{ere_object_id} aida:link _:blinkassertion{node_id} .
            _:blinkassertion{node_id} a aida:LinkAssertion .
            _:blinkassertion{node_id} aida:linkTarget "{reference_kb_id}:{node_id}" .
            _:blinkassertion{node_id} aida:system {system} .
            _:blinkassertion{node_id} aida:confidence _:blinkassertion{node_id}-confidence .
            _:blinkassertion{node_id}-confidence a aida:Confidence .
            _:blinkassertion{node_id}-confidence aida:confidenceValue '1.0'^^xsd:double .
            _:blinkassertion{node_id}-confidence aida:system {system} .
        """.format(ere_object_id = ere_object.get('id'),
                   reference_kb_id = reference_kb_id,
                   node_id = node_id,
                   system = SYSTEM_NAME
                   )
        link_assertion_triples.append(triples)
    
    # generate informative justification triples
    informative_justification_spans = ere_object.get('informative_justification_spans')
    informative_justification_triples = []
    for span in informative_justification_spans.values():
        if span is None:
            print('check this')
        triple = 'ldc:{ere_object_id} aida:informativeJustification _:b{span_md5} .'.format(ere_object_id=ere_object.get('id'),
                                                                                               span_md5=span.get('md5'))
        informative_justification_triples.append(triple)
    triples = """\
        ldc:{ere_object_id} a aida:{ere_type} .
        {informative_justification_triples}
        {ldc_time_assertion_triples}
        {link_assertion_triples}
        {has_name_triple}
        ldc:{ere_object_id} aida:system {system} .
    """.format(ere_object_id=ere_object.get('id'),
               ere_type = ere_type,
               ldc_time_assertion_triples = ldc_time_assertion_triples,
               informative_justification_triples = '\n'.join(informative_justification_triples),
               link_assertion_triples = '\n'.join(link_assertion_triples),
               has_name_triple = has_name_triple,
               system = SYSTEM_NAME,
               )
    return triples    

def generate_text_justification_triples(document_span):
    triples = """\
        _:b{md5} a aida:TextJustification .
        _:b{md5} aida:system {system} .
        _:b{md5} aida:source '{document_element_id}' .
        _:b{md5} aida:sourceDocument '{document_id}' .
        _:b{md5} aida:startOffset '{start_x}'^^xsd:int .
        _:b{md5} aida:endOffsetInclusive '{end_x}'^^xsd:int .
        _:b{md5} aida:confidence _:b{md5}_confidence .
        _:b{md5}_confidence aida:confidenceValue '1.0'^^xsd:double .
        _:b{md5}_confidence a aida:Confidence .
        _:b{md5}_confidence aida:system {system} .""".format(md5 = document_span.get('md5'),
                                                             system = SYSTEM_NAME,
                                                             document_id = document_span.get('document_id'),
                                                             document_element_id = document_span.get('document_element_id'),
                                                             start_x = document_span.get('span').get('start_x'),
                                                             end_x = document_span.get('span').get('end_x')
                                                             )
    return triples

def generate_image_justification_triples(document_span):
    triples = """\
        _:b{md5} a aida:ImageJustification .
        _:b{md5} aida:system {system} .
        _:b{md5} aida:source '{document_element_id}' .
        _:b{md5} aida:sourceDocument '{document_id}' .
        _:b{md5} aida:boundingBox _:b{md5}_boundingbox .
        _:b{md5}_boundingbox a aida:BoundingBox .
        _:b{md5}_boundingbox aida:boundingBoxUpperLeftX '{start_x}'^^xsd:int .
        _:b{md5}_boundingbox aida:boundingBoxUpperLeftY '{start_y}'^^xsd:int .
        _:b{md5}_boundingbox aida:boundingBoxLowerRightX '{end_x}'^^xsd:int .
        _:b{md5}_boundingbox aida:boundingBoxLowerRightY '{end_y}'^^xsd:int .
        _:b{md5} aida:confidence _:b{md5}_confidence .
        _:b{md5}_confidence aida:confidenceValue '1.0'^^xsd:double .
        _:b{md5}_confidence a aida:Confidence .
        _:b{md5}_confidence aida:system {system} .""".format(md5 = document_span.get('md5'),
                                                             system = SYSTEM_NAME,
                                                             document_id = document_span.get('document_id'),
                                                             document_element_id = document_span.get('document_element_id'),
                                                             start_x = document_span.get('span').get('start_x'),
                                                             start_y = document_span.get('span').get('start_y'),
                                                             end_x = document_span.get('span').get('end_x'),
                                                             end_y = document_span.get('span').get('end_y')
                                                             )
    return triples

def generate_keyframe_justification_triples(document_span):
    triples = """\
        _:b{md5} a aida:KeyFrameVideoJustification .
        _:b{md5} aida:system {system} .
        _:b{md5} aida:keyFrame '{keyframe_id}' .
        _:b{md5} aida:source '{document_element_id}' .
        _:b{md5} aida:sourceDocument '{document_id}' .
        _:b{md5} aida:boundingBox _:b{md5}_boundingbox .
        _:b{md5}_boundingbox a aida:BoundingBox .
        _:b{md5}_boundingbox aida:boundingBoxUpperLeftX '{start_x}'^^xsd:int .
        _:b{md5}_boundingbox aida:boundingBoxUpperLeftY '{start_y}'^^xsd:int .
        _:b{md5}_boundingbox aida:boundingBoxLowerRightX '{end_x}'^^xsd:int .
        _:b{md5}_boundingbox aida:boundingBoxLowerRightY '{end_y}'^^xsd:int .
        _:b{md5} aida:confidence _:b{md5}_confidence .
        _:b{md5}_confidence aida:confidenceValue '1.0'^^xsd:double .
        _:b{md5}_confidence a aida:Confidence .
        _:b{md5}_confidence aida:system {system} .""".format(md5 = document_span.get('md5'),
                                                             system = SYSTEM_NAME,
                                                             document_id = document_span.get('document_id'),
                                                             document_element_id = document_span.get('document_element_id'),
                                                             keyframe_id = document_span.get('keyframe_id'),
                                                             start_x = document_span.get('span').get('start_x'),
                                                             start_y = document_span.get('span').get('start_y'),
                                                             end_x = document_span.get('span').get('end_x'),
                                                             end_y = document_span.get('span').get('end_y')
                                                             )
    return triples

def generate_video_justification_triples(document_span, channel, generate_optional_channel_attribute_flag):
    channel_attribute_triple = ''
    if generate_optional_channel_attribute_flag:
        channel_attribute_triple = "_:b{md5} aida:channel '{channel}' .".format(md5 = document_span.get('md5'),
                                                                              channel = channel)
    triples = """\
        _:b{md5} a aida:VideoJustification .
        {channel_attribute_triple}
        _:b{md5} aida:system {system} .
        _:b{md5} aida:source '{document_element_id}' .
        _:b{md5} aida:sourceDocument '{document_id}' .
        _:b{md5} aida:startTimestamp '{start_x}'^^xsd:double .
        _:b{md5} aida:endTimestamp '{end_x}'^^xsd:double .
        _:b{md5} aida:confidence _:b{md5}_confidence .
        _:b{md5}_confidence aida:confidenceValue '1.0'^^xsd:double .
        _:b{md5}_confidence a aida:Confidence .
        _:b{md5}_confidence aida:system {system} .""".format(md5 = document_span.get('md5'),
                                                             channel_attribute_triple = channel_attribute_triple,
                                                             system = SYSTEM_NAME,
                                                             document_id = document_span.get('document_id'),
                                                             document_element_id = document_span.get('document_element_id'),
                                                             start_x = document_span.get('span').get('start_x'),
                                                             end_x = document_span.get('span').get('end_x')
                                                             )
    return triples

def generate_picture_channel_video_justification_triples(document_span, generate_optional_channel_attribute_flag=True):
    return generate_video_justification_triples(document_span, 'picture', generate_optional_channel_attribute_flag)

def generate_sound_channel_video_justification_triples(document_span, generate_optional_channel_attribute_flag=True):
    return generate_video_justification_triples(document_span, 'sound', generate_optional_channel_attribute_flag)

def generate_both_channels_video_justification_triples(document_span, generate_optional_channel_attribute_flag=True):
    return generate_video_justification_triples(document_span, 'both', generate_optional_channel_attribute_flag)

def generate_picture_justification_triples(document_span):
    triples = """\
        _:b{md5} a aida:PictureChannelVideoJustification .
        _:b{md5} aida:system {system} .
        _:b{md5} aida:source '{document_element_id}' .
        _:b{md5} aida:sourceDocument '{document_id}' .
        _:b{md5} aida:startTimestamp '{start_x}'^^xsd:double .
        _:b{md5} aida:endTimestamp '{end_x}'^^xsd:double .
        _:b{md5} aida:confidence _:b{md5}_confidence .
        _:b{md5}_confidence aida:confidenceValue '1.0'^^xsd:double .
        _:b{md5}_confidence a aida:Confidence .
        _:b{md5}_confidence aida:system {system} .""".format(md5 = document_span.get('md5'),
                                                             system = SYSTEM_NAME,
                                                             document_id = document_span.get('document_id'),
                                                             document_element_id = document_span.get('document_element_id'),
                                                             start_x = document_span.get('span').get('start_x'),
                                                             end_x = document_span.get('span').get('end_x')
                                                             )
    return triples

def generate_sound_justification_triples(document_span):
    triples = """\
        _:b{md5} a aida:SoundChannelVideoJustification .
        _:b{md5} aida:system {system} .
        _:b{md5} aida:source '{document_element_id}' .
        _:b{md5} aida:sourceDocument '{document_id}' .
        _:b{md5} aida:startTimestamp '{start_x}'^^xsd:double .
        _:b{md5} aida:endTimestamp '{end_x}'^^xsd:double .
        _:b{md5} aida:confidence _:b{md5}_confidence .
        _:b{md5}_confidence aida:confidenceValue '1.0'^^xsd:double .
        _:b{md5}_confidence a aida:Confidence .
        _:b{md5}_confidence aida:system {system} .""".format(md5 = document_span.get('md5'),
                                                             system = SYSTEM_NAME,
                                                             document_id = document_span.get('document_id'),
                                                             document_element_id = document_span.get('document_element_id'),
                                                             start_x = document_span.get('span').get('start_x'),
                                                             end_x = document_span.get('span').get('end_x')
                                                             )
    return triples

def generate_type_assertion_triples(mention):
    full_type = mention.get('full_type')
    type_assertion_md5 = get_md5_from_string('{id}:{full_type}'.format(id=mention.get('id'),
                                                                  full_type=full_type
                                                                  ))
    subject = mention.get('id')
    justified_by_triples = []
    for document_span in mention.get('document_spans').values():
        justified_by_triple = 'ldc:assertion-{type_assertion_md5} aida:justfiedBy _:b{document_span_md5} .'.format(type_assertion_md5=type_assertion_md5,
                                                                                                         document_span_md5=document_span.get('md5'))
        justified_by_triples.append(justified_by_triple)

    triples = """\
        ldc:assertion-{type_assertion_md5} a rdf:Statement .
        ldc:assertion-{type_assertion_md5} rdf:object ldcOnt:{full_type} .
        ldc:assertion-{type_assertion_md5} rdf:predicate rdf:type .
        ldc:assertion-{type_assertion_md5} rdf:subject ldc:{subject} .
        ldc:assertion-{type_assertion_md5} aida:confidence _:bta{type_assertion_md5}-confidence .
        _:bta{type_assertion_md5}-confidence a aida:Confidence .
        _:bta{type_assertion_md5}-confidence aida:confidenceValue '1.0'^^xsd:double .
        _:bta{type_assertion_md5}-confidence aida:system {system} .
        {justified_by_triples}
        ldc:assertion-{type_assertion_md5} aida:system {system} .
        """.format(type_assertion_md5 = type_assertion_md5,
                   full_type = full_type,
                   subject = subject,
                   system = SYSTEM_NAME,
                   justified_by_triples = '\n'.join(justified_by_triples)
                   )
    return triples

def generate_argument_assertions_with_single_contained_justification_triple(slot):
    subject = slot.get('subject')
    argument = slot.get('argument')
    subject_mention_id = subject.get('id')
    argument_mention_id = argument.get('id')
    slot_type = slot.get('slot_type')
    slot_assertion_md5 = get_md5_from_string('{}:{}:{}'.format(subject_mention_id, slot_type, argument_mention_id))
    subject_informative_justifications = subject.get('informative_justification_spans')
    for informative_justifications in [subject_informative_justifications]:
        if len(informative_justifications) != 1:
            slot.get('logger').record_event('UNEXPECTED_NUM_INF_JUSTIFICATIONS', slot.get_code_location())
    subject_informative_justification = list(subject_informative_justifications.values())[0]
    triples = """\
        ldc:assertion-{slot_assertion_md5} a rdf:Statement .
        ldc:assertion-{slot_assertion_md5} rdf:object ldc:{argument_mention_id} .
        ldc:assertion-{slot_assertion_md5} rdf:predicate ldcOnt:{slot_type} .
        ldc:assertion-{slot_assertion_md5} rdf:subject ldc:{subject_mention_id} .
        ldc:assertion-{slot_assertion_md5} aida:confidence _:bslotassertion-{slot_assertion_md5}-confidence .
        _:bslotassertion-{slot_assertion_md5}-confidence a aida:Confidence .
        _:bslotassertion-{slot_assertion_md5}-confidence aida:confidenceValue '1.0'^^xsd:double .
        _:bslotassertion-{slot_assertion_md5}-confidence aida:system {system} .
        ldc:assertion-{slot_assertion_md5} aida:justifiedBy _:bslotassertion-{slot_assertion_md5}-justification .
        _:bslotassertion-{slot_assertion_md5}-justification a aida:CompoundJustification . 
        _:bslotassertion-{slot_assertion_md5}-justification aida:containedJustification _:b{subject_informative_justification_md5} .
        _:bslotassertion-{slot_assertion_md5}-justification aida:confidence _:bslotassertion-{slot_assertion_md5}-justification-confidence .
        _:bslotassertion-{slot_assertion_md5}-justification-confidence a aida:Confidence .
        _:bslotassertion-{slot_assertion_md5}-justification-confidence aida:confidenceValue '1.0'^^xsd:double .
        _:bslotassertion-{slot_assertion_md5}-justification-confidence aida:system {system} .
        _:bslotassertion-{slot_assertion_md5}-justification aida:system {system} .
        ldc:assertion-{slot_assertion_md5} aida:system {system} .
        """.format(slot_assertion_md5 = slot_assertion_md5,
                   subject_mention_id = subject_mention_id,
                   argument_mention_id = argument_mention_id,
                   slot_type = slot_type,
                   subject_informative_justification_md5 = subject_informative_justification.get('md5'),
                   system = SYSTEM_NAME
                   )
    return triples

def generate_argument_assertions_with_two_contained_justifications_triple(slot):
    subject = slot.get('subject')
    argument = slot.get('argument')
    subject_mention_id = subject.get('id')
    argument_mention_id = argument.get('id')
    slot_type = slot.get('slot_type')
    slot_assertion_md5 = get_md5_from_string('{}:{}:{}'.format(subject_mention_id, slot_type, argument_mention_id))
    subject_informative_justifications = subject.get('informative_justification_spans')
    argument_informative_justifications = argument.get('informative_justification_spans')
    for informative_justifications in [subject_informative_justifications, argument_informative_justifications]:
        if len(informative_justifications) != 1:
            slot.get('logger').record_event('UNEXPECTED_NUM_INF_JUSTIFICATIONS', slot.get_code_location())
    subject_informative_justification = list(subject_informative_justifications.values())[0]
    argument_informative_justification = list(argument_informative_justifications.values())[0]
    triples = """\
        ldc:assertion-{slot_assertion_md5} a rdf:Statement .
        ldc:assertion-{slot_assertion_md5} rdf:object ldc:{argument_mention_id} .
        ldc:assertion-{slot_assertion_md5} rdf:predicate ldcOnt:{slot_type} .
        ldc:assertion-{slot_assertion_md5} rdf:subject ldc:{subject_mention_id} .
        ldc:assertion-{slot_assertion_md5} aida:confidence _:bslotassertion-{slot_assertion_md5}-confidence .
        _:bslotassertion-{slot_assertion_md5}-confidence a aida:Confidence .
        _:bslotassertion-{slot_assertion_md5}-confidence aida:confidenceValue '1.0'^^xsd:double .
        _:bslotassertion-{slot_assertion_md5}-confidence aida:system {system} .
        ldc:assertion-{slot_assertion_md5} aida:justifiedBy _:bslotassertion-{slot_assertion_md5}-justification .
        _:bslotassertion-{slot_assertion_md5}-justification a aida:CompoundJustification . 
        _:bslotassertion-{slot_assertion_md5}-justification aida:containedJustification _:b{subject_informative_justification_md5} .
        _:bslotassertion-{slot_assertion_md5}-justification aida:containedJustification _:b{argument_informative_justification_md5} .
        _:bslotassertion-{slot_assertion_md5}-justification aida:confidence _:bslotassertion-{slot_assertion_md5}-justification-confidence .
        _:bslotassertion-{slot_assertion_md5}-justification-confidence a aida:Confidence .
        _:bslotassertion-{slot_assertion_md5}-justification-confidence aida:confidenceValue '1.0'^^xsd:double .
        _:bslotassertion-{slot_assertion_md5}-justification-confidence aida:system {system} .
        _:bslotassertion-{slot_assertion_md5}-justification aida:system {system} .
        ldc:assertion-{slot_assertion_md5} aida:system {system} .
        """.format(slot_assertion_md5 = slot_assertion_md5,
                   subject_mention_id = subject_mention_id,
                   argument_mention_id = argument_mention_id,
                   slot_type = slot_type,
                   subject_informative_justification_md5 = subject_informative_justification.get('md5'),
                   argument_informative_justification_md5 = argument_informative_justification.get('md5'),
                   system = SYSTEM_NAME
                   )
    return triples

def generate_audio_justification_triples(document_span):
    triples = """\
        _:b{md5} a aida:AudioJustification .
        _:b{md5} aida:system {system} .
        _:b{md5} aida:source '{document_element_id}' .
        _:b{md5} aida:sourceDocument '{document_id}' .
        _:b{md5} aida:startTimestamp '{start_x}'^^xsd:double .
        _:b{md5} aida:endTimestamp '{end_x}'^^xsd:double .
        _:b{md5} aida:confidence _:b{md5}_confidence .
        _:b{md5}_confidence aida:confidenceValue '1.0'^^xsd:double .
        _:b{md5}_confidence a aida:Confidence .
        _:b{md5}_confidence aida:system {system} .""".format(md5 = document_span.get('md5'),
                                                             system = SYSTEM_NAME,
                                                             document_id = document_span.get('document_id'),
                                                             document_element_id = document_span.get('document_element_id'),
                                                             start_x = document_span.get('span').get('start_x'),
                                                             end_x = document_span.get('span').get('end_x')
                                                             )
    return triples

class AIFGenerator(Object):
    """
    AIDA AIF Generator
    """    
    def __init__(self, logger, annotations, reference_kb_id='LDC2019E44'):
        super().__init__(logger)
        self.annotations = annotations
        self.reference_kb_id = reference_kb_id
        self.triple_blocks = []
        self.generate_aif()
        
    def generate_aif(self):
        self.add_prefixes()
        print('--generating justifications ...')
        self.generate_justifications()
        print('--generating clusters ...')
        self.generate_clusters()
        print('--generating ere objects ...')
        self.generate_ere_objects()
        print('--generating type assertions ...')
        self.generate_type_assertions()
        print('--generating cluster memberships ...')
        self.generate_cluster_memberships()
        print('--generating argument assertions ...')
        self.generate_argument_assertions()
        print('--aif generation finished ...')

    def write_output(self, output_dir):
        filename = '{}/aif.txt'.format(output_dir)
        program_output = open(filename, 'w')
        aif = patch(self.get_aif())
        print('--writing output to file')
        program_output.write(aif)
        program_output.close()

    def get_aif(self, raw=False):
        raw_graph = '\n'.join(self.get('triple_blocks'))
        if raw:
            return raw_graph
        else:
            print("--parsing raw graph ...")
            g = Graph()
            g.parse(data=raw_graph, format="turtle")
            return g.serialize(format="turtle").decode('utf-8')
        
    def add_prefixes(self):
        prefixes = """\
            @prefix aida:  <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/InterchangeOntology#> .
            @prefix ldc:   <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LdcAnnotations#> .
            @prefix ldcOnt: <https://tac.nist.gov/tracks/SM-KBP/2019/ontologies/LDCOntology#> .
            @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
            @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
        """
        self.get('triple_blocks').append(prefixes)        
    
    def generate_argument_assertions(self):
        for slot in self.get('annotations').get('slots').values():
            # change generate_argument_assertions_with_single_contained_justification_triple 
            # to generate_argument_assertions_with_two_contained_justifications_triple
            # if two contained justifications were needed
            triple_block = generate_argument_assertions_with_single_contained_justification_triple(slot)
            self.get('triple_blocks').append(triple_block)
    
    def generate_ere_objects(self):
        for ere_object in self.get('annotations').get('mentions').values():
            triple_block = generate_ere_object_triples(self.get('reference_kb_id'), ere_object)
            self.get('triple_blocks').append(triple_block)
    
    def generate_clusters(self):
        for node in self.get('annotations').get('nodes').values():
            triple_block = generate_cluster_triples(self.get('reference_kb_id'), node)
            self.get('triple_blocks').append(triple_block)
    
    def generate_cluster_memberships(self):
        for node in self.get('annotations').get('nodes').values():
            triple_block = generate_cluster_membership_triples(node)
            self.get('triple_blocks').append(triple_block)
    
    def generate_justifications(self):
        for mention in self.get('annotations').get('mentions').values():
            for document_span in mention.get('document_spans').values():
                span_type = document_span.get('span_type')
                triple_block = None
                method_name = 'generate_{}_justification_triples'.format(span_type)
                generator = globals().get(method_name)
                if generator:
                    triple_block = generator(document_span)
                else:
                    self.get('logger').record_event('UNDEFINED_METHOD', method_name)
                self.get('triple_blocks').append(triple_block)
    
    def generate_type_assertions(self):
        for mention in self.get('annotations').get('mentions').values():
            triple_block = generate_type_assertion_triples(mention)
            self.get('triple_blocks').append(triple_block)
            
