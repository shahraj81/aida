#!/usr/bin/perl
use strict;

use GenerateQueriesManagerLib;

my $year = "2019";
my $postfix = "";
my $topic_id = "R103";
my $prevailing_theory_id = "pvth5";

my $logger = Logger->new();
my $error_filename = "$year/output_$topic_id\_$prevailing_theory_id$postfix/problems.log";
$logger->set_error_output($error_filename);
my $error_output = $logger->get_error_output();

my $ontology_mapping_entities_file = "2019/input/ontology/LDC_AIDAAnnotationOntologyWithMapping_V8_entities.tab";

my $prevailingtheory_data_files = Container->new("String");
$prevailingtheory_data_files->add("2019/input/prevailing-theories/Prevailing_theory_matrix_for_R103_sample_R103_pvth5.tab", "R103:pvth5");

#my $edge_data_files = Container->new("String");
#$edge_data_files->add("input/annotations-local/data/$topic_id$postfix/$topic_id\_evt_slots.tab");
#$edge_data_files->add("input/annotations-local/data/$topic_id$postfix/$topic_id\_rel_slots.tab");
#
#my $acceptable_relevance = Container->new("String");
#$acceptable_relevance->add("fully-relevant");

my $parameters = Parameters->new($logger);
$parameters->set("TOPICID", $topic_id);
$parameters->set("PREVAILING_THEORY_ID", $prevailing_theory_id);
$parameters->set("ONTOLOGY_MAPPING_ENTITIES_FILE", $ontology_mapping_entities_file);
$parameters->set("PREVAILING_THEORY_DATA_FILES", $prevailingtheory_data_files);
#$parameters->set("IGNORE_NIL", "true");
#$parameters->set("DOCUMENTIDS_MAPPING_FILE", "input/LDC2018E62.parent_children.tsv");
##$parameters->set("ROLE_MAPPING_FILE","input/nist-role-mapping.txt");
##$parameters->set("TYPE_MAPPING_FILE","input/nist-type-mapping.txt");
##$parameters->set("UID_INFO_FILE", "input/uid_info_LDC2018E62.tab");
##$parameters->set("HYPOTHESES_FILE", "input/annotations-local/data/$topic_id$postfix/$topic_id\_hypotheses.tab");
#$parameters->set("NODES_DATA_FILES", $nodes_data_files);
#$parameters->set("EDGES_DATA_FILES", $edge_data_files);
##$parameters->set("CANONICAL_MENTIONS_FILE", "input/canonical_mentions/canonical_mentions_$topic_id$postfix/$topic_id\_canonical_mentions.tsv");
$parameters->set("ERRORLOG_FILE", $error_filename);
$parameters->set("CLASS_QUERIES_XML_OUTPUT_FILE", "2019/output_$topic_id$postfix\_$prevailing_theory_id/class_queries.xml");
#$parameters->set("ZEROHOP_QUERIES_XML_OUTPUT_FILE", "output_$topic_id$postfix/$prevailing_theory_id\_zerohop_queries.xml");
#$parameters->set("GRAPH_QUERIES_XML_OUTPUT_FILE", "output_$topic_id$postfix/$prevailing_theory_id\_graph_queries.xml");
$parameters->set("CLASS_QUERIES_PREFIX", "AIDA_CL_2019");
#$parameters->set("ZEROHOP_QUERIES_PREFIX", "AIDA_ZH_2019");
#$parameters->set("GRAPH_QUERIES_SUBPREFIX", "AIDA_GR_2019");
#$parameters->set("EDGE_QUERIES_SUBPREFIX", "AIDA_EG_2019");

my $graph = Graph->new($logger, $parameters);
$graph->generate_queries();

my ($num_errors, $num_warnings) = $logger->report_all_information();
print "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
print "No problems encountered.\n" unless ($num_errors || $num_warnings);
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered\n";
exit 0;
