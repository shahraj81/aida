#!/usr/bin/perl
use strict;

use GenerateQueriesManagerLib;

my $logger = Logger->new();
my $error_filename = "output/problems.log";
$logger->set_error_output($error_filename);
my $error_output = $logger->get_error_output();

my $nodes_data_files = Container->new("String");
$nodes_data_files->add("input/annotations/data/T101/T101_ent_mentions.tab");
$nodes_data_files->add("input/annotations/data/T101/T101_evt_mentions.tab");
$nodes_data_files->add("input/annotations/data/T101/T101_rel_mentions.tab");

my $edge_data_files = Container->new("String");
$edge_data_files->add("input/annotations/data/T101/T101_evt_slots.tab");
$edge_data_files->add("input/annotations/data/T101/T101_rel_slots.tab");

my $acceptable_relevance = Container->new("String");
$acceptable_relevance->add("fully-relevant");
#$acceptable_relevance->add("partially-relevant");

my $parameters = Parameters->new($logger);
$parameters->set("DOCUMENTIDS_MAPPING_FILE", "input/DocumentIDsMappings.ttl");
$parameters->set("ROLE_MAPPING_FILE","input/nist-role-mapping.txt");
$parameters->set("TYPE_MAPPING_FILE","input/nist-type-mapping.txt");
$parameters->set("UID_INFO_FILE", "input/uid_info.tab");
$parameters->set("HYPOTHESES_FILE", "input/annotations/data/T101/T101_hypotheses.tab");
$parameters->set("NODES_DATA_FILES", $nodes_data_files);
$parameters->set("EDGES_DATA_FILES", $edge_data_files);
$parameters->set("ACCEPTABLE_RELEVANCE", $acceptable_relevance);
$parameters->set("CANONICAL_MENTIONS_FILE", "input/canonical_mentions/T101_canonical_mentions.tsv");
$parameters->set("IMAGES_BOUNDINGBOXES_FILE", "input/images_boundingboxes.tab");
$parameters->set("KEYFRAMES_BOUNDINGBOXES_FILE", "input/keyframes_boundingboxes.tab");
$parameters->set("ENCODINGFORMAT_TO_MODALITYMAPPING_FILE", "input/encodingformat_modality.tab");
$parameters->set("ERRORLOG_FILE", "output/problems.log");
$parameters->set("CLASS_QUERIES_XML_OUTPUT_FILE", "output/T101_class_queries.xml");
$parameters->set("ZEROHOP_QUERIES_XML_OUTPUT_FILE", "output/T101_zerohop_queries.xml");
$parameters->set("GRAPH_QUERIES_XML_OUTPUT_FILE", "output/T101_graph_queries.xml");
$parameters->set("CLASS_QUERIES_PREFIX", "AIDA_CL_2018");
$parameters->set("ZEROHOP_QUERIES_PREFIX", "AIDA_ZH_2018");
$parameters->set("GRAPH_QUERIES_PREFIX", "AIDA_GR_2018");

my $graph = Graph->new($logger, $parameters);
my %is_valid_entrypoint = %{$graph->get("LDC_NIST_MAPPINGS")->get("IS_VALID_ENTRYPOINT")};
my $keyframeboundingboxes = $graph->get("KEYFRAMES_BOUNDINGBOXES");
foreach my $node($graph->get("NODES")->toarray()) {
	my $node_id = $node->get("NODEID");
	foreach my $mention($node->get("MENTIONS")->toarray()) {
		my $mention_id = $mention->get("MENTIONID");
		my $enttype = $mention->get("NIST_TYPE");
		next unless (exists $is_valid_entrypoint{$enttype} && $is_valid_entrypoint{$enttype} eq "true");
		my $modality = $mention->get("MODALITY");
		my $type = $mention->get("TYPE");
		my $doceid = $mention->get("SPANS")->get("BY_INDEX", 0)->get("DOCUMENTEID");
		my $keyframe_id = "n/a";
		if($modality eq "video") {
			($keyframe_id) = $keyframeboundingboxes->get("KEYFRAMESIDS", $doceid);
		}
		elsif($modality eq "image") {
			$keyframe_id = $doceid;
		}
		print join("\t", ($node_id, $mention_id, $keyframe_id, "T101")), "\n"
			if ($enttype eq "Weapon" || $enttype eq "Vehicle" || $modality eq "video" || $modality eq "image" || $type ne "nam");
	}
}

$logger->report_all_information();
