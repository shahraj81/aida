"""
AIDA main script for generating queries
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "25 January 2022"

from aida.logger import Logger
from aida.file_handler import FileHandler

import argparse
import os
import sys

ALLOK_EXIT_CODE = 0
ERROR_EXIT_CODE = 255

def augment(n):
    augmented_value = '{}'.format(n)
    while len(augmented_value) < 4:
        augmented_value = '0{}'.format(augmented_value)
    return augmented_value

def check_paths(args):
    check_for_paths_existance([args.log_specifications, args.input])
    check_for_paths_non_existance([args.queries, args.sparql])

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

def clean(name_variant):
    cleaned_name_variant = name_variant.split(' (')[0]
    return cleaned_name_variant.strip()

def get_entrypoints(entry):
    entrypoints = {'name': {entry.get('entity_name').strip(): 1}}
    if entry.get('kbids') != 'N/A':
        entrypoints['kbid'] = {}
        kbids = entry.get('kbids')
        augmented_kbids = '|'.join(['REFKB:{}'.format(kbid.strip()) for kbid in kbids.split('|')])
        entrypoints['kbid'][augmented_kbids] = 1
    name_variants = entry.get('name_variants').strip()
    if name_variants != '':
        for name_variant in name_variants.split(','):
            cleaned_name_variant = clean(name_variant)
            if cleaned_name_variant != '':
                entrypoints['name'][cleaned_name_variant] = 1
    return entrypoints

def get_kbid_sparql_query_template():
    template = '''
PREFIX ldcOnt: <https://raw.githubusercontent.com/NextCenturyCorporation/AIDA-Interchange-Format/master/java/src/main/resources/com/ncc/aif/ontologies/LDCOntologyM36#>
PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX aida:  <https://raw.githubusercontent.com/NextCenturyCorporation/AIDA-Interchange-Format/master/java/src/main/resources/com/ncc/aif/ontologies/InterchangeOntology#>
PREFIX cfn:   <https://verdi.nextcentury.com/custom-function/>
PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>

# QueryID: <QUERYID>

SELECT DISTINCT
       ?docid                         # sourceDocument
       ?query_link_target             # link target as part of the query e.g. "Q84263196"
       ?link_target                   # link target in the KB matching ?query_link_target
       ?cluster                       # the ?cluster linked to ?link_target
       ?mention_span                  # informativeJustification span taken from the prototype of the ?cluster
       (str(?_j_cv) as ?j_cv)         # confidenceValue of informativeJustification
       (str(?_link_cv) as ?link_cv)   # confidenceValue of asserting that prototype of the ?cluster is the same as reference KB node ?link_target

WHERE {
    BIND ("<ENTRYPOINT>" AS ?query_link_target)

    ?cluster              a                             aida:SameAsCluster .
    ?cluster              aida:prototype                ?prototype .

    ?prototype            a                             aida:Entity .
    ?prototype            aida:informativeJustification ?justification .
    ?prototype            aida:link                     ?ref_kb_link .

    ?ref_kb_link          a                             aida:LinkAssertion .
    ?ref_kb_link          aida:linkTarget               ?link_target .
    ?ref_kb_link          aida:confidence               ?link_confidence .
    ?link_confidence      aida:confidenceValue          ?_link_cv .

    FILTER(cfn:memberOf(str(?link_target), str(?query_link_target))) .

    # Find mention spans for ?justification
    ?justification        aida:source                   ?doceid .
    ?justification        aida:sourceDocument           ?docid .
    ?justification        aida:confidence               ?j_confidence .
    ?j_confidence         aida:confidenceValue          ?_j_cv .

    OPTIONAL {
           ?justification a                             aida:TextJustification .
           ?justification aida:startOffset              ?so .
           ?justification aida:endOffsetInclusive       ?eo
    }
    OPTIONAL {
           ?justification a                             aida:ImageJustification .
           ?justification aida:boundingBox              ?bb1  .
           ?bb1           aida:boundingBoxUpperLeftX    ?ulx1 .
           ?bb1           aida:boundingBoxUpperLeftY    ?uly1 .
           ?bb1           aida:boundingBoxLowerRightX   ?lrx1 .
           ?bb1           aida:boundingBoxLowerRightY   ?lry1
    }
    OPTIONAL {
           ?justification a                             aida:KeyFrameVideoJustification .
           ?justification aida:keyFrame                 ?kfid .
           ?justification aida:boundingBox              ?bb2  .
           ?bb2           aida:boundingBoxUpperLeftX    ?ulx2 .
           ?bb2           aida:boundingBoxUpperLeftY    ?uly2 .
           ?bb2           aida:boundingBoxLowerRightX   ?lrx2 .
           ?bb2           aida:boundingBoxLowerRightY   ?lry2
    }
    OPTIONAL {
           ?justification a                             aida:ShotVideoJustification .
           ?justification aida:shot                     ?sid
    }
    OPTIONAL {
           ?justification a                             aida:AudioJustification .
           ?justification aida:startTimestamp           ?st1 .
           ?justification aida:endTimestamp             ?et1
    }
    OPTIONAL {
           ?justification a                             aida:VideoJustification .
           ?justification aida:startTimestamp           ?st2 .
           ?justification aida:endTimestamp             ?et2
    }

    BIND( IF( BOUND(?sid), ?sid, "__NULL__") AS ?_sid) .
    BIND( IF( BOUND(?kfid), ?kfid, "__NULL__") AS ?_kfid) .
    BIND( IF( BOUND(?so), ?so, "__NULL__") AS ?_so) .
    BIND( IF( BOUND(?eo), ?eo, "__NULL__") AS ?_eo) .
    BIND( COALESCE(?st1, ?st2, "__NULL__") AS ?_st) .
    BIND( COALESCE(?et1, ?et2, "__NULL__") AS ?_et) .
    BIND( COALESCE(?ulx1, ?ulx2, "__NULL__") AS ?_ulx) .
    BIND( COALESCE(?uly1, ?uly2, "__NULL__") AS ?_uly) .
    BIND( COALESCE(?lrx1, ?lrx2, "__NULL__") AS ?_lrx) .
    BIND( COALESCE(?lry1, ?lry2, "__NULL__") AS ?_lry) .

    BIND( cfn:getSpan(str(?docid), str(?doceid), str(?_sid), str(?_kfid), str(?_so), str(?_eo), str(?_ulx), str(?_uly), str(?_lrx), str(?_lry), str(?_st), str(?_et) ) AS ?mention_span ) .
}
ORDER BY ?docid ?cluster ?mention_span
'''
    return template

def get_name_sparql_query_template():
    template = '''
PREFIX ldcOnt: <https://raw.githubusercontent.com/NextCenturyCorporation/AIDA-Interchange-Format/master/java/src/main/resources/com/ncc/aif/ontologies/LDCOntologyM36#>
PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX aida:  <https://raw.githubusercontent.com/NextCenturyCorporation/AIDA-Interchange-Format/master/java/src/main/resources/com/ncc/aif/ontologies/InterchangeOntology#>
PREFIX cfn:   <https://verdi.nextcentury.com/custom-function/>
PREFIX xsd:   <http://www.w3.org/2001/XMLSchema#>

# QueryID: <QUERYID>

SELECT DISTINCT
       ?docid                         # sourceDocument
       ?query_link_target             # link target as part of the query e.g. "COVID-19"
       ?link_target                   # link target in the KB (taken from the value of hasName property of the member of the ?cluster) matching ?query_link_target
       ?cluster                       # the ?cluster that is associated with the ?link_target
       ?mention_span                  # informativeJustification span taken from the prototype of the ?cluster
       (str(?_j_cv) as ?j_cv)         # confidenceValue of informativeJustification
       (str(?_link_cv) as ?link_cv)   # confidenceValue of asserting that ?cluster has a ?member that is associated with the ?link_target

WHERE {
    BIND ("<ENTRYPOINT>" AS ?query_link_target)

    ?cluster              a                             aida:SameAsCluster .
    ?cluster              aida:prototype                ?prototype .

    ?prototype            a                             aida:Entity .
    ?prototype            aida:informativeJustification ?justification .

    ?statement            a                             aida:ClusterMembership .
    ?statement            aida:cluster                  ?cluster .
    ?statement            aida:clusterMember            ?member .
    ?statement            aida:confidence               ?cm_confidence .
    ?cm_confidence        aida:confidenceValue          ?_link_cv .

    ?member               aida:hasName                  ?link_target .

    FILTER( str(?link_target) = str(?query_link_target))

    # Find mention spans for ?inf_justification
    ?justification        aida:source                   ?doceid .
    ?justification        aida:sourceDocument           ?docid .
    ?justification        aida:confidence               ?j_confidence .
    ?j_confidence         aida:confidenceValue          ?_j_cv .

    OPTIONAL {
           ?justification a                             aida:TextJustification .
           ?justification aida:startOffset              ?so .
           ?justification aida:endOffsetInclusive       ?eo
    }
    OPTIONAL {
           ?justification a                             aida:ImageJustification .
           ?justification aida:boundingBox              ?bb1  .
           ?bb1           aida:boundingBoxUpperLeftX    ?ulx1 .
           ?bb1           aida:boundingBoxUpperLeftY    ?uly1 .
           ?bb1           aida:boundingBoxLowerRightX   ?lrx1 .
           ?bb1           aida:boundingBoxLowerRightY   ?lry1
    }
    OPTIONAL {
           ?justification a                             aida:KeyFrameVideoJustification .
           ?justification aida:keyFrame                 ?kfid .
           ?justification aida:boundingBox              ?bb2  .
           ?bb2           aida:boundingBoxUpperLeftX    ?ulx2 .
           ?bb2           aida:boundingBoxUpperLeftY    ?uly2 .
           ?bb2           aida:boundingBoxLowerRightX   ?lrx2 .
           ?bb2           aida:boundingBoxLowerRightY   ?lry2
    }
    OPTIONAL {
           ?justification a                             aida:ShotVideoJustification .
           ?justification aida:shot                     ?sid
    }
    OPTIONAL {
           ?justification a                             aida:AudioJustification .
           ?justification aida:startTimestamp           ?st1 .
           ?justification aida:endTimestamp             ?et1
    }
    OPTIONAL {
           ?justification a                             aida:VideoJustification .
           ?justification aida:startTimestamp           ?st2 .
           ?justification aida:endTimestamp             ?et2
    }

    BIND( IF( BOUND(?sid), ?sid, "__NULL__") AS ?_sid) .
    BIND( IF( BOUND(?kfid), ?kfid, "__NULL__") AS ?_kfid) .
    BIND( IF( BOUND(?so), ?so, "__NULL__") AS ?_so) .
    BIND( IF( BOUND(?eo), ?eo, "__NULL__") AS ?_eo) .
    BIND( COALESCE(?st1, ?st2, "__NULL__") AS ?_st) .
    BIND( COALESCE(?et1, ?et2, "__NULL__") AS ?_et) .
    BIND( COALESCE(?ulx1, ?ulx2, "__NULL__") AS ?_ulx) .
    BIND( COALESCE(?uly1, ?uly2, "__NULL__") AS ?_uly) .
    BIND( COALESCE(?lrx1, ?lrx2, "__NULL__") AS ?_lrx) .
    BIND( COALESCE(?lry1, ?lry2, "__NULL__") AS ?_lry) .

    BIND( cfn:getSpan(str(?docid), str(?doceid), str(?_sid), str(?_kfid), str(?_so), str(?_eo), str(?_ulx), str(?_uly), str(?_lrx), str(?_lry), str(?_st), str(?_et) ) AS ?mention_span ) .
}

ORDER BY ?docid ?cluster ?mention_span
'''
    return template

def get_sparql(logger, query_id, entrypoint_type, entrypoint):
    sparql_query = None
    if entrypoint_type == 'name':
        sparql_query = get_name_sparql_query_template()
    elif entrypoint_type == 'kbid':
        sparql_query = get_kbid_sparql_query_template()
    if sparql_query is None:
        logger.record_event('DEFAUL_CRITICAL_ERROR', 'Unexpected entrypoint_type')
    return sparql_query.replace('<QUERYID>', query_id).replace('<ENTRYPOINT>', entrypoint)

def main(args):
    logger = Logger(args.log, args.log_specifications, sys.argv)
    os.mkdir(args.sparql)
    columns = ['query_id', 'entity_id', 'entrypoint_type', 'entrypoint', 'clusters', 'documents']
    queries_fh = open(args.queries, 'w')
    queries_fh.write('{}\n'.format('\t'.join(columns)))
    query_num = 0
    for entry in FileHandler(logger, args.input):
        entity_id = entry.get('entity_id')
        entrypoints = get_entrypoints(entry)
        for entrypoint_type in entrypoints:
            for entrypoint in entrypoints[entrypoint_type]:
                query_num += 1
                values = {
                    'documents'      : args.documents,
                    'entity_id'      : entity_id,
                    'entrypoint_type': entrypoint_type,
                    'entrypoint'     : entrypoint,
                    'clusters'       : args.clusters,
                    'query_id'       : '{prefix}{query_num}'.format(prefix=args.prefix, query_num=augment(query_num))
                    }
                line = '\t'.join([values[column] for column in columns])
                queries_fh.write('{}\n'.format(line))
                sparql_query_fh = open('{dir}/{query_id}.rq'.format(dir=args.sparql, query_id=values['query_id']), 'w')
                sparql_query_fh.write(get_sparql(logger,
                                                 values['query_id'],
                                                 values['entrypoint_type'],
                                                 values['entrypoint']))
                sparql_query_fh.close()
    queries_fh.close()
    exit(ALLOK_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Align system and gold clusters")
    parser.add_argument('-c', '--clusters', default='1', help='Specify the number of clusters to be used for pooling (default: %(default)s)')
    parser.add_argument('-d', '--documents', default='10', help='Specify the number of documents per cluster to be used for pooling (default: %(default)s)')
    parser.add_argument('-l', '--log', default='log.txt', help='Specify a file to which log output should be redirected (default: %(default)s)')
    parser.add_argument('-p', '--prefix', default='AIDA_P3_TA2_E', help='Specify the prefix of SPARQL query files (default: %(default)s)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__, help='Print version number and exit')
    parser.add_argument('log_specifications', type=str, help='File containing error specifications')
    parser.add_argument('input', type=str, help='Input file containing information needed for generation of queries')
    parser.add_argument('queries', type=str, help='Specify the flattened queries file.')
    parser.add_argument('sparql', type=str, help='Specify a directory to SPAQRL queries should be written.')
    args = parser.parse_args()
    check_paths(args)
    main(args)