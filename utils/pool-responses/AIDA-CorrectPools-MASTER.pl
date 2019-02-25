#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use PoolResponsesManagerLib;
use POSIX;

### DO INCLUDE
##################################################################################### 
# This program takes as input: 
#   (1) A single pooler output file.
# and produces a corrected file as output. 
#
# The following corrections are made:
#   (1) Check if keyframe IDs are legal,
#   (2) Check if text spans are within bound,
#   (3) Check if for video/image spans, top-left x,y is above bottom-right x,y
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
my $switches = SwitchProcessor->new($0, "Apply corrections to the single pool file for LDC",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");

$switches->addParam("keyframes_boundingboxes", "required", "File containing keyframe bounding boxes");
$switches->addParam("images_boundingboxes", "required", "File containing image bounding boxes");
$switches->addParam("sentence_boundaries", "required", "File containing sentence boundaries");
$switches->addParam("pool", "required", "File containing pool");
$switches->addParam("output", "required", "Output file containing corrected pool");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("keyframes_boundingboxes"),
					$switches->get("images_boundingboxes"),
					$switches->get("sentence_boundaries"),
					$switches->get("pool"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

my $pool_filename = $switches->get("pool");
$logger->NIST_die("$pool_filename does not exist") unless -e $pool_filename;

my $output_filename = $switches->get("output");
$logger->NIST_die("$output_filename already exists")
	if(-e $output_filename);
open($program_output, ">:utf8", $output_filename)
	or $logger->NIST_die("Could not open $output_filename: $!");

my $keyframes_boundingboxes_filename = $switches->get("keyframes_boundingboxes");
my $images_boundingboxes_filename = $switches->get("images_boundingboxes");
my $sentence_boundaries_filename = $switches->get("sentence_boundaries");

my $pool = Pool->new($logger, $pool_filename);
my $keyframes_boundingboxes = KeyFramesBoundingBoxes->new($logger, $keyframes_boundingboxes_filename);
my $images_boundingboxes = ImagesBoundingBoxes->new($logger, $images_boundingboxes_filename);
my $text_document_boundaries = TextDocumentBoundaries->new($logger, $sentence_boundaries_filename);

print $program_output "KBID\tCLASS\tID\tMODALITY\tDOCID\tSPAN\tCORRECTNESS\tTYPE\n";
foreach my $node_id($pool->get("ALL_KEYS")) {
	foreach my $kit_entry($pool->get("BY_KEY", $node_id)->toarray()) {
		my @elements = split(/\t/, $kit_entry);
		my $mention_span = $elements[5];
		my ($id, $sx, $sy, $ex, $ey) = $mention_span =~ /^(.*?):\((\d+)\,(\d+)\)-\((\d+)\,(\d+)\)$/;
		$logger->record_problem("IGNORED", $kit_entry, {FILENAME => __FILE__, LINENUM => __LINE__})
			if($sx>$ex || $sy>$ey);
		if($id =~ /^(.*?)\_(\d+)$/){
			my ($doceid, $shot_num) = ($1, $2);
			unless($keyframes_boundingboxes->exists($id)) {
				my $new_id = $doceid . "_" . ($shot_num-1);
				if($keyframes_boundingboxes->exists($new_id)) {
					my $old_id = $id;
					$id = $new_id;
					my $corrected_mention_span = "$id:($sx,$sy)-($ex,$ey)";
					$elements[5] = $corrected_mention_span;
					$kit_entry = join("\t", @elements);
					$logger->record_problem("KEYFRAMEID_CORRECTED", $old_id, $id, 
					{FILENAME => __FILE__, LINENUM => __LINE__});
				}
			}
		}
		if($keyframes_boundingboxes->exists($id)) {
			my $keyframe_boundingbox = $keyframes_boundingboxes->get("BY_KEY", $id);
			unless ($keyframe_boundingbox->validate($mention_span)) {
				($sx, $sy, $ex, $ey) 
					= map {$keyframe_boundingbox->get($_)} 
						qw(TOP_LEFT_X TOP_LEFT_Y BOTTOM_RIGHT_X BOTTOM_RIGHT_Y);
				my $boundary = "($sx,$sy)-($ex,$ey)";
				my $corrected_mention_span = "$id:($sx,$sy)-($ex,$ey)";
				$elements[5] = $corrected_mention_span;
				$kit_entry = join("\t", @elements);
				$logger->record_problem("BOUNDINGBOX_OFF_BOUNDARY", $mention_span, $boundary, $corrected_mention_span, 
					{FILENAME => __FILE__, LINENUM => __LINE__});
			}
		}
		elsif($images_boundingboxes->exists($id)) {
			my $image_boundingbox = $images_boundingboxes->get("BY_KEY", $id);
			unless ($image_boundingbox->validate($mention_span)) {
				($sx, $sy, $ex, $ey)
					= map {$image_boundingbox->get($_)} 
						qw(TOP_LEFT_X TOP_LEFT_Y BOTTOM_RIGHT_X BOTTOM_RIGHT_Y);
				my $boundary = "($sx,$sy)-($ex,$ey)";
				my $corrected_mention_span = "$id:($sx,$sy)-($ex,$ey)";
				$elements[5] = $corrected_mention_span;
				$kit_entry = join("\t", @elements);
				$logger->record_problem("BOUNDINGBOX_OFF_BOUNDARY", $mention_span, $boundary, $corrected_mention_span, 
					{FILENAME => __FILE__, LINENUM => __LINE__});
			}
		}
		elsif(my $text_document_boundary = $text_document_boundaries->get("BOUNDARY", $mention_span)) {
			my $modified_flag = 0;
			my ($tb_start_char, $tb_end_char)
				= map {$text_document_boundary->get($_)}
					qw(START_CHAR END_CHAR);
			if($sx < $tb_start_char) {
				$sx = $tb_start_char;
				$modified_flag = 1;
			}
			if($ex > $tb_end_char) {
				$ex = $tb_end_char;
				$modified_flag = 1;
			}
			if($modified_flag) {
				my $doc_boundary = "$tb_start_char-$tb_end_char";
				my $corrected_mention_span = "$id:($sx,$sy)-($ex,$ey)";
				$elements[5] = $corrected_mention_span;
				$kit_entry = join("\t", @elements);
				$logger->record_problem("MENTION_OFF_BOUNDARY", $mention_span, $doc_boundary, $corrected_mention_span, 
					{FILENAME => __FILE__, LINENUM => __LINE__});
			}
		}
		else{
			$logger->record_problem("IGNORED", $kit_entry, {FILENAME => __FILE__, LINENUM => __LINE__});
			next;
		}
		print $program_output "$kit_entry\n";
	}
}

my ($num_errors, $num_warnings) = $logger->report_all_information();

unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;

