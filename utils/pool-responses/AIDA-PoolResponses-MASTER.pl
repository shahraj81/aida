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
$switches->addVarSwitch('types', "Colon-separated list of query types to be used for pooling");
$switches->put('types', "class:zerohop");
$switches->addParam("parameters", "required", "File containing required parameters");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

my $parameters_file = $switches->get("parameters");
$logger->NIST_die("$parameters_file does not exist")
	unless -e $parameters_file;

my $parameters = Parameters->new($logger, $parameters_file);	

my $types = $switches->get("types");
my $types_container = Container->new($logger);
foreach my $type_selected(split(/:/, $types)) {
	$logger->NIST_die("selected type \'$type_selected\' is not a valid type")
		unless $type{$type_selected};
	$types_container->add("KEY", $type_selected);
}
$logger->NIST_die("selected type \'graph\' can't be combined with other types")
	if($types_container->exists("graph") && 
		($types_container->exists("class") || $types_container->exists("zerohop")));
$parameters->set("TYPES", $types_container);

my @file_keys = qw(CLASS_QUERIES_DTD ZEROHOP_QUERIES_DTD GRAPH_QUERIES_DTD 
										CLASS_QUERIES_XML ZEROHOP_QUERIES_XML GRAPH_QUERIES_XML
										CLASS_RESPONSES_DTD ZEROHOP_RESPONSES_DTD GRAPH_RESPONSES_DTD
										CLASS_RESPONSES_XML ZEROHOP_RESPONSES_XML GRAPH_RESPONSES_XML
										MAPPINGS_FILE);

foreach my $path(map {$parameters->get($_)} @file_keys) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

my $output_filename = $parameters->get("OUTPUT_FILE");
$logger->NIST_die("$output_filename already exists") if -e $output_filename;

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

my $docid_mappings_file = $parameters->get("MAPPINGS_FILE");
my $docid_mappings = DocumentIDsMappings->new($logger, $docid_mappings_file);
my $pooled_responses = Container->new($logger);
foreach my $selected_type($types_container->toarray()) {
	my $queries_dtd_file = $parameters->get($type{$selected_type}{QUERIES_DTD_PARAMETER});
	my $queries_xml_file = $parameters->get($type{$selected_type}{QUERIES_XML_PARAMETER});
	my $queries = QuerySet->new($logger, $queries_dtd_file, $queries_xml_file);

	my $query_type = $queries_dtd_file;
	$query_type =~ s/^(.*?\/)+//g; $query_type =~ s/.dtd//;

	my $responses_dtd_file = $parameters->get($type{$selected_type}{RESPONSES_DTD_PARAMETER});
	my $responses_xml_dir = $parameters->get($type{$selected_type}{RESPONSES_XML_PARAMETER});
	my @response_xml_files = <$responses_xml_dir/*/*_responses.xml>;

	foreach my $response_xml_file(@response_xml_files) {
		$response_xml_file =~ /(^.*\/)+(.*?\..*?_responses.xml)/;
		my ($path, $filename) = ($1, $2);
		my ($source_docid) = $filename =~ /^(.*?)\..*?_responses.xml/;
		$source_docid = undef if $source_docid eq "TA2";
		my $scope = "withindoc";
		$scope = "withincorpus" unless $source_docid;
		my $validated_responses = ResponseSet->new($logger, $queries, $docid_mappings, $responses_dtd_file, $response_xml_file, $scope);
		next if $logger->get_num_problems();
		if($query_type eq "class_query" || $query_type eq "zerohop_query") {
			foreach my $response($validated_responses->get("RESPONSES")->toarray()) {
				my $query_id = $response->get("QUERYID");
				my $enttype = $queries->get("QUERY", $query_id)->get("ENTTYPE");
				foreach my $justification($response->get("JUSTIFICATIONS")->toarray()) {
					my $mention_span = $justification->tostring();
					my $mention_modality = $justification->get("MODALITY");
					my @docids = $justification->get("DOCIDS", $docid_mappings, $scope);
					@docids = grep {$_ eq $source_docid} @docids if $source_docid;
					$logger->record_problem("ACROSS_DOCUMENT_JUSTIFICATION", $source_docid, $justification->get("WHERE"))
						unless scalar @docids;
					foreach my $docid(@docids) {
						my $value = join("\t", ($query_id, $enttype, "<ID>", $mention_modality, $docid, $mention_span, "NIL", "NIL"));
						my $key = &main::generate_uuid_from_string($value);
						if($pooled_responses->exists($key)) {
							my $where = $justification->get("WHERE");
							$logger->record_debug_information("DUPLICATE_IN_POOLED_RESPONSE", "\n$value\n", $where);
						}
						else {
							$pooled_responses->add($value, $key);
						}
					}
				}
			}
		}
		elsif($query_type eq "graph_query") {
			
		}
		else {
			# TODO: unknown query tyoe - throw an exception
		}
	}
}

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
