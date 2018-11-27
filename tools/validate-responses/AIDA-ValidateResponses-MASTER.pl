#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ValidateResponsesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program takes as input: 
#   (1) an XML query file along with corresponding DTD file,
#   (2) A file listing mappings between DocumentID to DocumentElementID, and
#   (3) an XML response file along with corresponding DTD file, 
# and produces as output a validated XML response file.
#
# Author: Shahzad Rajput
# Please send questions or comments to shahzadrajput "at" gmail "dot" com
#
# For usage, run with no arguments
##################################################################################### 

my $version = "2018.0.3";

# Filehandles for program and error output
my $program_output = *STDOUT{IO};
my $error_output = *STDERR{IO};

# Validation code
my $validation_retval = 0;

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Validate XML response file",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addConstantSwitch('no_error_code', 'false', "Do not return any error code if problems are encountered?");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
$switches->addParam("sentence_boundaries", "required", "File containing sentence boundaries");
$switches->addParam("images_boundingboxes", "required", "File containing image bounding boxes");
$switches->addParam("keyframes_boundingboxes", "required", "File containing keyframe bounding boxes");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("responses_dtd", "required", "DTD file corresponding to the XML file containing response");
$switches->addParam("responses_xml", "required", "XML file containing responses");
$switches->addParam("output", "required", "Validated responses file");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("docid_mappings"), 
					$switches->get("sentence_boundaries"),
					$switches->get("images_boundingboxes"),
					$switches->get("keyframes_boundingboxes"),
					$switches->get("queries_dtd"),
					$switches->get("queries_xml"),
					$switches->get("responses_dtd"),
					$switches->get("responses_xml"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
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

my $docid_mappings_filename = $switches->get("docid_mappings");
my $sentence_boundaries_filename = $switches->get("sentence_boundaries");
my $images_boundingboxes_filename = $switches->get("images_boundingboxes");
my $keyframes_boundingboxes_filename = $switches->get("keyframes_boundingboxes");

my $docid_mappings = DocumentIDsMappings->new($logger, $docid_mappings_filename);
my $text_document_boundaries = TextDocumentBoundaries->new($logger, $sentence_boundaries_filename);
my $images_boundingboxes = ImagesBoundingBoxes->new($logger, $images_boundingboxes_filename);
my $keyframes_boundingboxes = KeyFramesBoundingBoxes->new($logger, $keyframes_boundingboxes_filename);

my $queries = QuerySet->new($logger, $switches->get("queries_dtd"), $switches->get("queries_xml"));
my $validated_responses = ResponseSet->new($logger, 
														$queries, 
														$docid_mappings, 
														$text_document_boundaries, 
														$images_boundingboxes, 
														$keyframes_boundingboxes, 
														$switches->get("responses_dtd"), 
														$switches->get("responses_xml"));
my ($num_errors, $num_warnings) = $logger->report_all_information();
$validation_retval = $Logger::NIST_error_code if(!$switches->get("no_error_code") && $num_errors+$num_warnings);
unless($num_errors) {
	print $program_output $validated_responses->tostring(2)
		if defined $program_output;
}
unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No problems encountered.\n" unless ($num_errors || $num_warnings);
}
print $error_output ($num_warnings || 'No'), " problems", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit $validation_retval;