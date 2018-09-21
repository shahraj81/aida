#!/usr/bin/perl
use strict;

use GenerateQueriesManagerLib;

my $logger = Logger->new();
my $error_filename = "problems.log";
$logger->set_error_output($error_filename);
my $error_output = $logger->get_error_output();

my %keyframeid_filename_mapping;
my $filehandler = FileHandler->new($logger, "input/masterShotBoundary.msb");
foreach my $entry($filehandler->get("ENTRIES")->toarray()) {
	my $filename = $entry->get("filename");
	my $keyframe_id = $entry->get("keyframe_id");
	$keyframeid_filename_mapping{$filename} = $keyframe_id;
}

$filehandler = FileHandler->new($logger, "input/canonical_mentions/canonical_mentions_P103_Q002_H001_1hop_LDC/P101_P102_P103_canonical_mentions.tsv");
foreach my $entry($filehandler->get("ENTRIES")->toarray()) {
	my $node_id = $entry->get("kb_id");
	my $mention_id = $entry->get("entitymention_id");
	my $filename = $entry->get("filename");
	$filename =~ s/\_\d+\..*?$//;
	my $keyframe_id = "n/a";
	$keyframe_id = $keyframeid_filename_mapping{$filename} if $keyframeid_filename_mapping{$filename};
	my $topic_id = $entry->get("topic");
	
	print join("\t", ($node_id, $mention_id, $keyframe_id, $topic_id)), "\n";
}