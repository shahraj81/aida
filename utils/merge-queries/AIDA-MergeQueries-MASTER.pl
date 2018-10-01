#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use MergeQueriesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program takes as input a set of XML query files corresponding to different
# hypotheses along with a single corresponding DTD file and produce as output a 
# single queries file.
#
# Author: Shahzad Rajput
# Please send questions or comments to shahzadrajput "at" gmail "dot" com
#
# For usage, run with no arguments
##################################################################################### 

my $version = "2018.0.0";

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Merge query files into a single one.",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("output_map", "required", "Output file containing the mappings between new queryids to old queryids and filename");
$switches->addParam("output_xml", "required", "Output XML query file");
$switches->addParam("files", "required", "all others", "File(s) containing XML query files to be merged.");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
my $error_output = $logger->get_error_output();

foreach my $path(($switches->get("docid_mappings"), $switches->get("queries_dtd"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

foreach my $path(($switches->get("output_xml"), $switches->get("output_map"))) {
	$logger->NIST_die("$path already exists") if -e $path;
}

my $xml_query_files = Container->new($logger, "RAW");
foreach my $xml_query_file(@{$switches->get("files")}) {
	$logger->NIST_die("$xml_query_file does not exist") unless -e $xml_query_file;
	$xml_query_files->add($xml_query_file);
}

my (%query_uuids, $outermost_tag);
my $query_dtd_file = $switches->get("queries_dtd");
my $xml_output_file = $switches->get("output_xml");
my $map_output_file = $switches->get("output_map");
my $output_type = $query_dtd_file;
$output_type =~ s/^(.*?\/)+//g;
$output_type =~ s/.dtd//;
$outermost_tag = "class_queries" if $output_type eq "class_query";
$outermost_tag = "zerohop_queries" if $output_type eq "zerohop_query";
$outermost_tag = "graph_queries" if $output_type eq "graph_query";
open(my $program_output_map, ">:utf8", $map_output_file)
	or $logger->record_problem('MISSING_FILE', $map_output_file, $!);
print $program_output_map "new_query_id\told_query_id\tfile\n";
open(my $program_output_xml, ">:utf8", $xml_output_file) 
	or $logger->record_problem('MISSING_FILE', $xml_output_file, $!);
print $program_output_xml "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
print $program_output_xml "<$outermost_tag>\n";
my $query_num = 0;
foreach my $query_xml_file(@{$switches->get("files")}){
	my $xml_filehandler = XMLFileHandler->new($logger, $query_dtd_file, $query_xml_file);
	while(my $query = $xml_filehandler->get("NEXT_OBJECT")) {
		$query_num++;
		my $query_string = $query->tostring(2);
		my ($query_id) = $query_string =~ /query id=\"(.*?)\"/;
		$query_string =~ s/query id=\".*?\"/query id=\"QUERYID\"/;
		$query_string =~ s/\n\s*?\# Query: AIDA.*?\s*\n/\n\n\t\# Query: QUERYID\n\n/;
		my $uuid = &main::generate_uuid_from_string($query_string);
		if ($query_uuids{$uuid}) {
			my $where = {FILENAME => __FILE__, LINENUM => __LINE__};
			$logger->record_debug_information("DUPLICATE_QUERY", 
					$query_id, $query_xml_file, 
					$query_uuids{$uuid}{QUERYID}, $query_uuids{$uuid}{FILENAME},
					$where);
			next;
		}
		my $query_id_prefix;
		if($output_type eq "class_query" || $output_type eq "zerohop_query") {
			($query_id_prefix) = $query_id =~ /^(.*?)_(\d+)$/;
		}
		elsif($output_type eq "graph_query") {
			($query_id_prefix) = $query_id =~ /^(.*?)_(\d+)_(\d+)$/;
		}
		else {
			my $where = {FILENAME => __FILE__, LINENUM => __LINE__};
			$logger->record_problem("UNKNOWN_OUTPUT_TYPE", $output_type, $where);
		}
		my $new_query_id = "$query_id_prefix\_$query_num";
		$query_string =~ s/QUERYID/$new_query_id/g;
		$query_uuids{$uuid} = {QUERYID => $query_id, FILENAME => $query_xml_file};
		print $program_output_map "$new_query_id\t$query_id\t$query_xml_file\n";
		print $program_output_xml $query_string;
	}
}
print $program_output_xml "<\/$outermost_tag>\n";
close($program_output_xml);
close($program_output_map);
	
my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($switches->get('error_file') eq "STDERR") {
	print "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
