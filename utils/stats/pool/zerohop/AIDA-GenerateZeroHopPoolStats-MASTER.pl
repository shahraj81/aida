#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ZeroHopPoolStatsManagerLib;

### DO INCLUDE
##################################################################################### 
# This program generates the stats of zerohop pool.
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
my $switches = SwitchProcessor->new($0, "Generate stats of the zerohop pool",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "The official XML file containing queries");
$switches->addParam("ldc_queries", "required", "XML file containing queries having LDC nodeids");
$switches->addParam("responses_dtd", "required", "DTD file corresponding to the XML file containing response");
$switches->addParam("responses_xml", "required", "File containing path to XML response files being pooled");
$switches->addParam("pool", "required", "The file containing pooled responses");
$switches->addParam("output", "required", "Output file");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("docid_mappings"),
					$switches->get("queries_dtd"),
					$switches->get("queries_xml"),
					$switches->get("ldc_queries"),
					$switches->get("responses_dtd"),
					$switches->get("responses_xml"),
					$switches->get("pool"))) {
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
	
my $docid_mappings_file = $switches->get("docid_mappings");
my $queries_dtd_file = $switches->get("queries_dtd");
my $queries_xml_file = $switches->get("queries_xml");
my $ldc_queries_xml_file = $switches->get("ldc_queries");
my $responses_dtd_file = $switches->get("responses_dtd");
my $responses_xml_pathfile = $switches->get("responses_xml");
my $pool_filename = $switches->get("pool");
my $query_type = $queries_dtd_file;
$query_type =~ s/^(.*?\/)+//g; $query_type =~ s/.dtd//;

my $docid_mappings = DocumentIDsMappings->new($logger, $docid_mappings_file);
my $queries = QuerySet->new($logger, $queries_dtd_file, $queries_xml_file);
my $ldc_queries = QuerySet->new($logger, $queries_dtd_file, $ldc_queries_xml_file);

$logger->NIST_die("$pool_filename does not exist") unless -e $pool_filename;
my $pool = Pool->new($logger, $pool_filename);

my %system_responses;
foreach my $responses_xml_filename(@responses_xml_filenames) {
	print STDERR "--processing: $responses_xml_filename\n";
	my ($system_id, $system_type, $hypothesis_id);
	$hypothesis_id = "NIL";
	if($responses_xml_filename =~ /LDC_run/) {
		$system_id = "LDC";
		if($responses_xml_filename =~ /LDC_P103_(TA\d)_ZEROHOP/) {
			$system_type = $1;
			if($system_type eq "TA1") {
				$system_type = "task1a";
			}
			elsif($system_type eq "TA2") {
				$system_type = "task2";
			}
			else{
				$system_type = "NIL";
			}
		}
	}
	else{
		my @elements = split(/\//, $responses_xml_filename);
		$system_id = $elements[6];
		$system_type = $elements[5];
		$system_type =~ s/-responses$//;
		$hypothesis_id = $elements[7] if $system_type eq "task1b";
	}

	my $responses = ResponseSet->new($logger, $queries, $docid_mappings, $responses_dtd_file, $responses_xml_filename);
	foreach my $response($responses->toarray()) {
		my $query_id = $response->get("QUERYID");
		next unless $ldc_queries->exists($query_id);
		my $node_id = $ldc_queries->get("QUERY", $query_id)->get("ENTRYPOINT")->get("NODE");
		$node_id =~ s/^\?//;
		foreach my $justification($response->get("JUSTIFICATIONS")->toarray()) {
			my $mention_span = $justification->tostring();
			my $key = "$node_id:$mention_span";
			$system_responses{$key}{"$system_id-$hypothesis_id-$system_type"} = 1;
		}
	}
}

my %stats;
foreach my $node_id($pool->get("ALL_KEYS")) {
	foreach my $kit_entry($pool->get("BY_KEY", $node_id)->toarray()) {
		my @elements = split(/\t/, $kit_entry);
		my ($node_id, $modality, $mention_span) = ($elements[0], $elements[3], $elements[5]);
		my $key = "$node_id:$mention_span";
		foreach my $system_info(keys %{$system_responses{$key}}) {
			my ($system_id, $hypothesis_id, $system_type) = split(/\-/, $system_info);
			$stats{$node_id}{$system_id . "-" . $hypothesis_id . "-" . $system_type}{$modality}++;
			$stats{$node_id}{$system_id . "-" . $hypothesis_id . "-" . $system_type}{"ALL"}++;
		}
		$stats{$node_id}{"ALL"}{$modality}++;
		$stats{"ALL"}{"ALL"}{$modality}++;
		$stats{"ALL"}{"ALL"}{"ALL"}++;
	}
}

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors+$num_warnings) {
	print $program_output "node_id\tsystem\tmodality\tcount\n";
	foreach my $node_id(sort keys %stats) {
		foreach my $system(sort keys %{$stats{$node_id}}) {
			foreach my $modality(sort keys %{$stats{$node_id}{$system}}){
				my $count = $stats{$node_id}{$system}{$modality};
				print $program_output "$node_id\t$system\t$modality\t$count\n";
			}
		}
	}
}

unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
