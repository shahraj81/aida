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

my $version = "2018.0.0";

# Filehandles for program and error output
my $program_output = *STDOUT{IO};
my $error_output = *STDERR{IO};

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
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
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
					$switches->get("queries_dtd"),
					$switches->get("queries_xml"),
					$switches->get("responses_dtd"),
					$switches->get("responses_xml"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

foreach my $path(($switches->get("output"))) {
	$logger->NIST_die("$path already exists") if -e $path;
}

my $output_filename = $switches->get("output");
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

my $docid_mappings = DocumentIDsMappings->new($logger, $switches->get("docid_mappings"));
my $queries = QuerySet->new($logger, $switches->get("queries_dtd"), $switches->get("queries_xml"));
my $validated_responses = ResponseSet->new($logger, $queries, $docid_mappings, $switches->get("responses_dtd"), $switches->get("responses_xml"));
	
my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors) {
	print $program_output $validated_responses->tostring()
		if defined $program_output;
}
unless($switches->get('error_file') eq "STDERR") {
	print "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
