#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use PoolResponsesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program takes as input: 
#   (1) an XML query file along with corresponding DTD file,
#   (2) A file listing mappings between DocumentID to DocumentElementID, and
#   (3) a set of XML response file(s) along with DTD file corresponding to response file(s), 
# and produces as output a pool of distinct responses to be used for assessment by LDC.
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
my $switches = SwitchProcessor->new($0, "Pool XML response files",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addConstantSwitch("increment", "true", "If output file exists, do you wish to use it to build the pool incrementally?");
$switches->addVarSwitch("ldc_queries", "XML query file sent to LDC? Required for zerohop queries, optional otherwise");
$switches->put('ldc_queries', "none");
$switches->addVarSwitch("k", "Top k responses to be pooled from within each document");
$switches->put('k', "10");
$switches->addParam("coredocs", "required", "List of core documents to be included in the pool");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("responses_dtd", "required", "DTD file corresponding to the XML file containing response");
$switches->addParam("responses_xml", "required", "File containing path to XML response files being pooled");
$switches->addParam("output", "required", "Output file");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("coredocs"),
					$switches->get("docid_mappings"),
					$switches->get("queries_dtd"),
					$switches->get("queries_xml"),
					$switches->get("ldc_queries"),
					$switches->get("responses_dtd"),
					$switches->get("responses_xml"))) {
	next if $path eq "none";
	$logger->NIST_die("$path does not exist") unless -e $path;
}

my $filehandler = FileHandler->new($logger, $switches->get("responses_xml"));
my $entries = $filehandler->get("ENTRIES");
foreach my $entry($entries->toarray()) {
	my $path = $entry->get("filename");
	$logger->NIST_die("$path does not exist") unless -e $path;
}

my $output_filename = $switches->get("output");
my $incremental_build = $switches->get("increment");
my $existing_pool;
unless($incremental_build) {
	$logger->NIST_die("$output_filename already exists")
		if(-e $output_filename);
}
else {
	if(-e $output_filename) {
		$existing_pool = Pool->new($logger, $output_filename);
		system("rm $output_filename");
	}
}

open($program_output, ">:utf8", $output_filename)
	or $logger->NIST_die("Could not open $output_filename: $!");
	
# Container to store pooled responses
my $pooled_responses;

my $k = $switches->get("k");
my $coredocs_file = $switches->get("coredocs");
my $docid_mappings_file = $switches->get("docid_mappings");
my $queries_dtd_file = $switches->get("queries_dtd");
my $queries_xml_file = $switches->get("queries_xml");
my $ldc_queries_xml_file = $switches->get("ldc_queries");
my $responses_dtd_file = $switches->get("responses_dtd");
my $responses_xml_pathfile = $switches->get("responses_xml");
my $query_type = $queries_dtd_file;
$query_type =~ s/^(.*?\/)+//g; $query_type =~ s/.dtd//;

my $coredocs = CoreDocs->new($logger, $coredocs_file);
my $docid_mappings = DocumentIDsMappings->new($logger, $docid_mappings_file);
my $queries = QuerySet->new($logger, $queries_dtd_file, $queries_xml_file);
my $ldc_queries = QuerySet->new($logger, $queries_dtd_file, $ldc_queries_xml_file);

$pooled_responses = ResponsesPool->new($logger, $k, $coredocs, $docid_mappings, $queries, $ldc_queries, $responses_dtd_file, $responses_xml_pathfile, $existing_pool);

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors+$num_warnings) {
	$pooled_responses->write_output($program_output);
}

unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
