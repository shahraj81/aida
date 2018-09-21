#!/usr/bin/perl
use strict;

use GenerateQueriesManagerLib;

my $postfix = "_Q002_H001_1hop_LDC";
my $topic_id = "P103";

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
#$acceptable_relevance->add("partially-relevant");

my $parameters = Parameters->new($logger);
$parameters->set("DOCUMENTIDS_MAPPING_FILE", "input/LDC2018E62.parent_children.ttl");
$parameters->set("ROLE_MAPPING_FILE","input/nist-role-mapping.txt");
$parameters->set("TYPE_MAPPING_FILE","input/nist-type-mapping.txt");
$parameters->set("UID_INFO_FILE", "input/uid_info_LDC2018E62.tab");
$parameters->set("HYPOTHESES_FILE", "input/annotations-local/data/$topic_id$postfix/$topic_id\_hypotheses.tab");
$parameters->set("NODES_DATA_FILES", $nodes_data_files);
$parameters->set("EDGES_DATA_FILES", $edge_data_files);
$parameters->set("ACCEPTABLE_RELEVANCE", $acceptable_relevance);
$parameters->set("CANONICAL_MENTIONS_FILE", "input/canonical_mentions/canonical_mentions_$topic_id$postfix/$topic_id\_canonical_mentions.tsv");
$parameters->set("IMAGES_BOUNDINGBOXES_FILE", "input/images_boundingboxes.tab");
$parameters->set("KEYFRAMES_BOUNDINGBOXES_FILE", "input/keyframes_boundingboxes.tab");
$parameters->set("ENCODINGFORMAT_TO_MODALITYMAPPING_FILE", "input/encodingformat_modality.tab");
$parameters->set("ERRORLOG_FILE", $error_filename);

my $graph = Graph->new($logger, $parameters);
my %is_valid_entrypoint = %{$graph->get("LDC_NIST_MAPPINGS")->get("IS_VALID_ENTRYPOINT")};
my $keyframeboundingboxes = $graph->get("KEYFRAMES_BOUNDINGBOXES");

my $output_filename = $parameters->get("CANONICAL_MENTIONS_FILE");
open(my $program_output, ">:utf8", $output_filename) or die("Could not open $output_filename: $!");

print $program_output join("\t", ("node_id", "mention_id", "keyframe_id", "topic_id")), "\n";
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
		print $program_output join("\t", ($node_id, $mention_id, $keyframe_id, "T101")), "\n"
			if ($enttype eq "Weapon" || $enttype eq "Vehicle" || $modality eq "video" || $modality eq "image" || $type eq "nam");
	}
}

close($program_output);

my ($num_errors, $num_warnings) = $logger->report_all_information();
print "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
print "No problems encountered.\n" unless ($num_errors || $num_warnings);
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered\n";
exit 0;
