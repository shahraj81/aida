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

our %scope = (
  withindoc => {
    DESCRIPTION => "All justifications in a response file should come from a single corpus document",
  },
  withincorpus => {
    DESCRIPTION => "All justifications in a response file should come from a corpus document",
  },
  anywhere => {
    DESCRIPTION => "Justifications may come from anywhere.",
  });

our %type = (
  class => {
  	QUERIES_DTD_PARAMETER => "CLASS_QUERIES_DTD",
  	RESPONSES_DTD_PARAMETER => "CLASS_RESPONSES_DTD",
  	QUERIES_XML_PARAMETER => "CLASS_QUERIES_XML",
  	RESPONSES_XML_PARAMETER => "CLASS_RESPONSES_XML",
    DESCRIPTION => "Class query and response",
  },
  zerohop => {
  	QUERIES_DTD_PARAMETER => "ZEROHOP_QUERIES_DTD",
  	RESPONSES_DTD_PARAMETER => "ZEROHOP_RESPONSES_DTD",
  	QUERIES_XML_PARAMETER => "ZEROHOP_QUERIES_XML",
  	RESPONSES_XML_PARAMETER => "ZEROHOP_RESPONSES_XML",
    DESCRIPTION => "Zerohop query and response",
  },
  graph => {
  	QUERIES_DTD_PARAMETER => "GRAPH_QUERIES_DTD",
  	RESPONSES_DTD_PARAMETER => "GRAPH_RESPONSES_DTD",
  	QUERIES_XML_PARAMETER => "GRAPH_QUERIES_XML",
  	RESPONSES_XML_PARAMETER => "GRAPH_RESPONSES_XML",
    DESCRIPTION => "Graph query and response",
  });

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Pool XML response files",
												"-types is a colon-separated list drawn from:\n" . &main::build_documentation(\%type) .
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addVarSwitch('maxkitsize', "How large can the kit be? This value is provided by LDC.");
$switches->put('maxkitsize', "200");
$switches->addVarSwitch("ldc_queries_xml", "XML query file sent to LDC? Required for zerohop queries, optional otherwise");
$switches->put('ldc_queries_xml', "none");
$switches->addParam("coredocs", "required", "List of core documents to be included in the pool");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("responses_dtd", "required", "DTD file corresponding to the XML file containing response");
$switches->addParam("responses_xml", "required", "File containing path to XML response files being pooled");
$switches->addParam("k", "required", "Top k responses to be pooled");
$switches->addParam("output", "required", "Output directory");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("coredocs"),
					$switches->get("docid_mappings"),
					$switches->get("queries_dtd"),
					$switches->get("queries_xml"),
					$switches->get("ldc_queries_xml"),
					$switches->get("responses_dtd"),
					$switches->get("responses_xml"))) {
	next if $path eq "none";
	$logger->NIST_die("$path does not exist") unless -e $path;
}

my $output_dir = $switches->get("output");
$logger->NIST_die("$output_dir already exists")
	if(-e $output_dir);

#if ($output_filename eq 'none') {
#  undef $program_output;
#}
#elsif (lc $output_filename eq 'stdout') {
#  $program_output = *STDOUT{IO};
#}
#elsif (lc $output_filename eq 'stderr') {
#  $program_output = *STDERR{IO};
#}
#else {
#  open($program_output, ">:utf8", $output_filename) or $logger->NIST_die("Could not open $output_filename: $!");
#}

# Container to store pooled responses
my $pooled_responses;

my $maxkitsize = $switches->get("maxkitsize");
my $coredocs_file = $switches->get("coredocs");
my $docid_mappings_file = $switches->get("docid_mappings");
my $queries_dtd_file = $switches->get("queries_dtd");
my $queries_xml_file = $switches->get("queries_xml");
my $ldc_queries_xml_file = $switches->get("ldc_queries_xml");
my $responses_dtd_file = $switches->get("responses_dtd");
my $responses_xml_pathfile = $switches->get("responses_xml");
my $query_type = $queries_dtd_file;
$query_type =~ s/^(.*?\/)+//g; $query_type =~ s/.dtd//;

my $coredocs = CoreDocs->new($logger, $coredocs_file);
my $docid_mappings = DocumentIDsMappings->new($logger, $docid_mappings_file);
my $queries = QuerySet->new($logger, $queries_dtd_file, $queries_xml_file);
my $ldc_queries = QuerySet->new($logger, $queries_dtd_file, $ldc_queries_xml_file);

$pooled_responses = ResponsesPool->new($logger, $coredocs, $docid_mappings, $queries, $ldc_queries, $responses_dtd_file, $responses_xml_pathfile);
$pooled_responses->write_output($output_dir);


#
#foreach my $selected_type($types_container->toarray()) {
#	
#
#	
#	
#
#	$parameters->get($type{$selected_type}{RESPONSES_DTD_PARAMETER});
#	my $responses_xml_dir = $parameters->get($type{$selected_type}{RESPONSES_XML_PARAMETER});
#	my @response_xml_files = <$responses_xml_dir/*/*_responses.xml>;
#
#	foreach my $response_xml_file(@response_xml_files) {
#		$response_xml_file =~ /(^.*\/)+(.*?\..*?_responses.xml)/;
#		my ($path, $filename) = ($1, $2);
#		my ($source_docid) = $filename =~ /^(.*?)\..*?_responses.xml/;
#		$source_docid = undef if $source_docid eq "TA2";
#		my $scope = "withindoc";
#		$scope = "withincorpus" unless $source_docid;
#		my $validated_responses = ResponseSet->new($logger, $queries, $docid_mappings, $responses_dtd_file, $response_xml_file, $scope);
#		next if $logger->get_num_problems();
#		if($query_type eq "class_query" || $query_type eq "zerohop_query") {
#			foreach my $response($validated_responses->get("RESPONSES")->toarray()) {
#				my $query_id = $response->get("QUERYID");
#				my $enttype = $queries->get("QUERY", $query_id)->get("ENTTYPE");
#				foreach my $justification($response->get("JUSTIFICATIONS")->toarray()) {
#					my $mention_span = $justification->tostring();
#					my $mention_modality = $justification->get("MODALITY");
#					my @docids = $justification->get("DOCIDS", $docid_mappings, $scope);
#					@docids = grep {$_ eq $source_docid} @docids if $source_docid;
#					$logger->record_problem("ACROSS_DOCUMENT_JUSTIFICATION", $source_docid, $justification->get("WHERE"))
#						unless scalar @docids;
#					foreach my $docid(@docids) {
#						my $value = join("\t", ($query_id, $enttype, "<ID>", $mention_modality, $docid, $mention_span, "NIL", "NIL"));
#						my $key = &main::generate_uuid_from_string($value);
#						if($pooled_responses->exists($key)) {
#							my $where = $justification->get("WHERE");
#							$logger->record_debug_information("DUPLICATE_IN_POOLED_RESPONSE", "\n$value\n", $where);
#						}
#						else {
#							$pooled_responses->add($value, $key);
#						}
#					}
#				}
#			}
#		}
#		elsif($query_type eq "graph_query") {
#			
#		}
#		else {
#			# TODO: unknown query tyoe - throw an exception
#		}
#	}
#}

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors+$num_warnings) {
	# TODO: print header
	my $i = 0;
	foreach my $pooled_response(sort $pooled_responses->toarray()) {
		$i++;
		$pooled_response =~ s/<ID>/$i/;
		print $program_output "$pooled_response\n"
			if defined $program_output;
	}
}

unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
