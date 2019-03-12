#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ResolveQueriesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program applies AIDA queries to KBs in order to generate submissions.
# It takes as input the evaluation queries, a directory containing KBs
# split across TTL files in case of a TA1 submission, and a output directory. 
# In case of a TA2 systems, the submission is in the form of a single TTL file. 
#
# Author: Shahzad Rajput
# Please send questions or comments to shahzadrajput "at" gmail "dot" com
#
# For usage, run with no arguments
##################################################################################### 

my $version = "2019.0.0";

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Apply a set of SPARQL evaluation queries to a knowledge base \
											in Turtle RDF format to produce AIDA output for assessment.",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addConstantSwitch("split_queries", "true", "Run SPARQL queries");
$switches->addConstantSwitch("apply_queries", "true", "Run SPARQL queries");
$switches->addConstantSwitch("xml_output", "true", "Convert SPARQL output to XML");
$switches->addVarSwitch('graphdb', "Specify path to SPARQL executable");
$switches->put('graphdb', "none");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("input", "required", "File containing the KB (for TA2 system) or directory containing KBs (for TA1 system).");
$switches->addParam("intermediate", "required", "Specify a directory to be used for storing intermediate files.");
$switches->addParam("output", "required", "Specify an output directory.");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
my $error_output = $logger->get_error_output();

foreach my $path(($switches->get("sparql"), 
									$switches->get("docid_mappings"), 
									$switches->get("queries_dtd"), 
									$switches->get("queries_xml"), 
									$switches->get("input"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

foreach my $path(($switches->get("intermediate"), $switches->get("output"))) {
	$logger->NIST_die("$path already exists") if -e $path;
}

my $parameters = Parameters->new($logger);
$parameters->set("DOCUMENTIDS_MAPPING_FILE", $switches->get("docid_mappings"));
$parameters->set("QUERIES_DTD_FILE", $switches->get("queries_dtd"));
$parameters->set("QUERIES_XML_FILE", $switches->get("queries_xml"));
$parameters->set("INPUT", $switches->get("input"));
$parameters->set("INTERMEDIATE_DIR", $switches->get("intermediate"));
$parameters->set("OUTPUT_DIR", $switches->get("output"));
$parameters->set("GRAPHDB", $switches->get("grapdh"));

my $queries = Queries->new($logger, $parameters);
# Generate RQ files
$queries->generate_sparql_query_files() if($switches->get("split_queries"));
# Resolve queries against KB(s)
$queries->apply_sparql_queries() if($switches->get("apply_queries"));
# Convert sparql output to XML
$queries->convert_output_files_to_xml() if($switches->get("xml_output"));

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($switches->get('error_file') eq "STDERR") {
	print "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
