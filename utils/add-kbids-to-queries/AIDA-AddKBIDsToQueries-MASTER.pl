#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use AddKBIDsToQueriesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program takes as input: 
#   (1) an XML query file along with corresponding DTD file, 
#   (2) entity mention file from LDC's annotations, 
#   (3) File containing keyframe bounding boxex,
#   (4) File containing image bounding boxes,
#   (5) canonical_mentions file from LDC, and
#   (6) annotation files from LDC for reading KBID to mention spans.
# and produces as output an XML query file with all the variables replaced with
# corresponding KBIDs.
#
# Author: Shahzad Rajput
# Please send questions or comments to shahzadrajput "at" gmail "dot" com
#
# For usage, run with no arguments
##################################################################################### 

my $version = "2018.0.0";

# Filehandles for program and error output
my $program_output = *STDOUT{IO};
my $error_output = *STDERR{IO};

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Add KBIDs to variables in queries",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("canonical_mentions", "required", "Canonical mentions file as received from LDC");
$switches->addParam("keyframes_boundingboxes", "required", "File containing keyframe bounding boxes");
$switches->addParam("images_boundingboxes", "required", "File containing image bounding boxes");
$switches->addParam("topic_id", "required", "Topic ID");
$switches->addParam("output", "required", "The output XML query file with all the variables replaced with corresponding KBIDs");
$switches->addParam("mentions", "required", "all others", "Entity mentions file(s) from LDC's annotations");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("queries_dtd"),
					$switches->get("queries_xml"),
					$switches->get("canonical_mentions"),
					$switches->get("keyframes_boundingboxes"),
					$switches->get("images_boundingboxes"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

my $the_topic_id = $switches->get("topic_id");

my $entity_mention_files = Container->new($logger, "RAW");
foreach my $entity_mention_file(@{$switches->get("mentions")}) {
	$logger->NIST_die("$entity_mention_file does not exist") unless -e $entity_mention_file;
	$entity_mention_files->add($entity_mention_file);
}

my $output_filename = $switches->get("output");
$logger->NIST_die("$output_filename already exists")
	if(-e $output_filename);

if ($output_filename eq 'none') {
  undef $program_output;
}
elsif (lc $output_filename eq 'stdout') {
  $program_output = *STDOUT{IO};
}
elsif (lc $output_filename eq 'stderr') {
  $program_output = *STDERR{IO};
}
else {
  open($program_output, ">:utf8", $output_filename) or $logger->NIST_die("Could not open $output_filename: $!");
}

# Load the bounding boxes information
my $keyframes_boundingboxes = KeyFramesBoundingBoxes->new($logger, $switches->get("keyframes_boundingboxes"));
my $images_boundingboxes = ImagesBoundingBoxes->new($logger, $switches->get("images_boundingboxes"));

# Load canonical mentions
my %canonical_mentions;
my $filehandler = FileHandler->new($logger, $switches->get("canonical_mentions"));
foreach my $entry($filehandler->get("ENTRIES")->toarray()) {
	my $kb_id = $entry->get("node_id");
	my $mention_id = $entry->get("mention_id");
	my $keyframe_id = $entry->get("keyframe_id");
	my $topic_id = $entry->get("topic_id"); 
	$canonical_mentions{$mention_id} = {KEYFRAMEID=>$keyframe_id, KBID=>$kb_id}
		if $topic_id eq $the_topic_id;
}

# Load mentions
my %mentions;
foreach my $entity_mention_file($entity_mention_files->toarray()) {
	my $filehandler = FileHandler->new($logger, $entity_mention_file);
	foreach my $entry($filehandler->get("ENTRIES")->toarray()) {
		my $mention_id = $entry->get("entitymention_id");
		next unless $canonical_mentions{$mention_id};
		my $kb_id = $entry->get("kb_id");
		$logger->NIST_die("kb_ids don't match for mention $mention_id")
			if($kb_id ne $canonical_mentions{$mention_id}{KBID});
		my $keyframe_id = $canonical_mentions{$mention_id}{KEYFRAMEID};
		my $provenance = $entry->get("provenance");
		my $start = $entry->get("textoffset_startchar");
		my $end = $entry->get("textoffset_endchar");
		if($start eq "" && $end eq "") {
			# Find the start and end from image or keyframe bounding box
			if($keyframe_id ne "n/a") {
				$start = $keyframes_boundingboxes->get("BY_KEY", $keyframe_id)->get("START");
				$end = $keyframes_boundingboxes->get("BY_KEY", $keyframe_id)->get("END");
				$provenance = $keyframe_id;
			}
			else {
				$start = $images_boundingboxes->get("BY_KEY", $provenance)->get("START");
				$end = $images_boundingboxes->get("BY_KEY", $provenance)->get("END");
			}
		}
		else {
			$start = "$start,0";
			$end = "$end,0";
		}
		$mentions{"$provenance:($start)-($end)"}{$kb_id} = 1;
	}
}

my $queries = QuerySet->new($logger, $switches->get("queries_dtd"), $switches->get("queries_xml"));
foreach my $query($queries->get("QUERIES")->toarray()) {
	my $mention = $query->get("ENTRYPOINT")->get("DESCRIPTOR")->tostring();
	my @kb_ids = keys %{$mentions{$mention}};
	die "Multiple kbids for mention: $mention" if @kb_ids > 1;
	die "No kbid for mention: $mention" unless @kb_ids;
	my $kb_id = $kb_ids[0];
	$query->get("ENTRYPOINT")->set("NODE", $kb_id);
	my $node_xml_object = $query->get("XML_OBJECT")->get("CHILD", "node");
	$node_xml_object->set("ELEMENT", $kb_id);
}
	
my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors) {
	print $program_output $queries->tostring(2)
		if defined $program_output;
}
unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
