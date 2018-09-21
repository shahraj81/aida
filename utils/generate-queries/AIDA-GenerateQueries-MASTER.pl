#!/usr/bin/perl
use strict;

use GenerateQueriesManagerLib;

my $postfix = "_Q002_H001_1hop_LDC";
my $topic_id = "P103";
my $hypothesis_id = "P103_Q002_H001";

my $logger = Logger->new();
my $error_filename = "output_$topic_id$postfix/problems.log";
$logger->set_error_output($error_filename);
my $error_output = $logger->get_error_output();

my $nodes_data_files = Container->new("String");
$nodes_data_files->add("input/annotations-local/data/$topic_id$postfix/$topic_id\_ent_mentions.tab");
$nodes_data_files->add("input/annotations-local/data/$topic_id$postfix/$topic_id\_evt_mentions.tab");
$nodes_data_files->add("input/annotations-local/data/$topic_id$postfix/$topic_id\_rel_mentions.tab");

my $edge_data_files = Container->new("String");
$edge_data_files->add("input/annotations-local/data/$topic_id$postfix/$topic_id\_evt_slots.tab");
$edge_data_files->add("input/annotations-local/data/$topic_id$postfix/$topic_id\_rel_slots.tab");

my $acceptable_relevance = Container->new("String");
$acceptable_relevance->add("fully-relevant");

my $parameters = Parameters->new($logger);
$parameters->set("TOPICID", $topic_id);
$parameters->set("HYPOTHESISID", $hypothesis_id);
$parameters->set("IGNORE_NIL", "true");
$parameters->set("DOCUMENTIDS_MAPPING_FILE", "input/LDC2018E62.parent_children.tsv");
$parameters->set("ROLE_MAPPING_FILE","input/nist-role-mapping.txt");
$parameters->set("TYPE_MAPPING_FILE","input/nist-type-mapping.txt");
$parameters->set("UID_INFO_FILE", "input/uid_info_LDC2018E62.tab");
$parameters->set("HYPOTHESES_FILE", "input/annotations-local/data/$topic_id$postfix/$topic_id\_hypotheses.tab");
$parameters->set("NODES_DATA_FILES", $nodes_data_files);
$parameters->set("EDGES_DATA_FILES", $edge_data_files);
$parameters->set("ACCEPTABLE_RELEVANCE", $acceptable_relevance);
$parameters->set("IMAGES_BOUNDINGBOXES_FILE", "input/images_boundingboxes.tab");
$parameters->set("KEYFRAMES_BOUNDINGBOXES_FILE", "input/keyframes_boundingboxes.tab");
$parameters->set("ENCODINGFORMAT_TO_MODALITYMAPPING_FILE", "input/encodingformat_modality.tab");
$parameters->set("CANONICAL_MENTIONS_FILE", "input/canonical_mentions/canonical_mentions_$topic_id$postfix/P101_P102_P103_canonical_mentions_fixed_1.tsv");
#$parameters->set("CANONICAL_MENTIONS_FILE", "input/canonical_mentions/canonical_mentions_$topic_id$postfix/$topic_id\_canonical_mentions.tsv");
$parameters->set("ERRORLOG_FILE", $error_filename);
$parameters->set("CLASS_QUERIES_XML_OUTPUT_FILE", "output_$topic_id$postfix/$hypothesis_id\_class_queries.xml");
$parameters->set("ZEROHOP_QUERIES_XML_OUTPUT_FILE", "output_$topic_id$postfix/$hypothesis_id\_zerohop_queries.xml");
$parameters->set("GRAPH_QUERIES_XML_OUTPUT_FILE", "output_$topic_id$postfix/$hypothesis_id\_graph_queries.xml");
$parameters->set("CLASS_QUERIES_PREFIX", "AIDA_CL_2018");
$parameters->set("ZEROHOP_QUERIES_PREFIX", "AIDA_ZH_2018");
$parameters->set("GRAPH_QUERIES_SUBPREFIX", "AIDA_GR_2018");
$parameters->set("EDGE_QUERIES_SUBPREFIX", "AIDA_EG_2018");

my $graph = Graph->new($logger, $parameters);
$graph->generate_queries();

my ($num_errors, $num_warnings) = $logger->report_all_information();
print "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
print "No problems encountered.\n" unless ($num_errors || $num_warnings);
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered\n";
exit 0;
