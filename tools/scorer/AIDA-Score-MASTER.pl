#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ScoreManagerLib;

### DO INCLUDE
##################################################################################### 
# This program scores responses against the QREL.
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
my $switches = SwitchProcessor->new($0, "Score XML response files",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addVarSwitch('queries', "File containing query IDs to be scored");
$switches->addVarSwitch('runid', "Run ID of the system being scored");
$switches->put('runid', "system");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("coredocs", "required", "List of core documents to be included in the pool");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "The official XML file containing queries");
$switches->addParam("ldc_queries", "required", "XML file containing queries having LDC nodeids");
$switches->addParam("responses_dtd", "required", "DTD file corresponding to the XML file containing response");
$switches->addParam("responses_xml", "required", "File containing path to all the XML response files belonging to a run/submission to be scored");
$switches->addParam("qrel", "required", "QREL file");
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
					$switches->get("responses_xml"),
					$switches->get("qrel"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

my (@responses_xml_filenames, $filehandler, $entries);
$filehandler = FileHandler->new($logger, $switches->get("responses_xml"));
$entries = $filehandler->get("ENTRIES");
foreach my $entry($entries->toarray()) {
	my $path = $entry->get("filename");
	$logger->NIST_die("$path does not exist") unless -e $path;
	push(@responses_xml_filenames, $path);
}

my $output_filename = $switches->get("output");
$logger->NIST_die("$output_filename already exists")
	if(-e $output_filename);
open($program_output, ">:utf8", $output_filename)
	or $logger->NIST_die("Could not open $output_filename: $!");
	
my $coredocs_file = $switches->get("coredocs");
my $docid_mappings_file = $switches->get("docid_mappings");
my $queries_dtd_file = $switches->get("queries_dtd");
my $queries_xml_file = $switches->get("queries_xml");
my $ldc_queries_xml_file = $switches->get("ldc_queries");
my $responses_dtd_file = $switches->get("responses_dtd");
my $responses_xml_pathfile = $switches->get("responses_xml");
my $qrel_filename = $switches->get("qrel");
my $runid = $switches->get("runid");
my $query_type = $queries_dtd_file;
$query_type =~ s/^(.*?\/)+//g; $query_type =~ s/.dtd//;

my $coredocs = CoreDocs->new($logger, $coredocs_file);
my $docid_mappings = DocumentIDsMappings->new($logger, $docid_mappings_file);
my $queries = QuerySet->new($logger, $queries_dtd_file, $queries_xml_file);
my $ldc_queries = QuerySet->new($logger, $queries_dtd_file, $ldc_queries_xml_file);

my $queries_to_score_filename = $switches->get("queries");
my @queries_to_score;
if($queries_to_score_filename) {
	$logger->NIST_die("$queries_to_score_filename does not exist") unless -e $queries_to_score_filename;
	$filehandler = FileHandler->new($logger, $queries_to_score_filename);
	$entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my $query_id = $entry->get("QUERYID");
		push(@queries_to_score, $query_id);
	}
}
else {
	foreach my $query($ldc_queries->get("QUERIES")->toarray()) {
		my $query_id = $query->get("QUERYID");
		push(@queries_to_score, $query_id);
	}
}

my $responses = ResponseSet->new($logger, $queries, $docid_mappings, $responses_dtd_file, @responses_xml_filenames);
my $assessments = QREL->new($logger, $qrel_filename, $query_type);
my $scorer = ScoresManager->new($logger, $runid, $ldc_queries, $responses, $assessments, $query_type, @queries_to_score);

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors+$num_warnings) {
	print $program_output $scorer->print_lines($program_output);
}

unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
