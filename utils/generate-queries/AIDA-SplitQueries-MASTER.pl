#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use GenerateQueriesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program splits AIDA XML queries into multiple .rq files.
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
my $switches = SwitchProcessor->new($0, "Split Queries.",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("output", "required", "Specify an output directory.");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
my $error_output = $logger->get_error_output();

foreach my $path(($switches->get("queries_dtd"), 
									$switches->get("queries_xml"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

foreach my $path(($switches->get("output"))) {
	$logger->NIST_die("$path already exists") if -e $path;
}

system("mkdir -p " . $switches->get("output"));
my $xml_filehandler = XMLFileHandler->new($logger, $switches->get("queries_dtd"), $switches->get("queries_xml"));
while(my $query = $xml_filehandler->get("NEXT_OBJECT")) {
	my ($query_id) = $query->get("ATTRIBUTES")->toarray();
	my ($sparql_query_string) = $query->get("CHILD", "sparql")->get("ELEMENT") =~ /\<\!\[CDATA\[(.*?)\]\]\>/gs;
	my $filename = $switches->get("output") . "/$query_id.rq";
	open(my $program_output, ">:utf8", $filename)
		or $logger->record_problem('MISSING_FILE', $filename, $!);
	$sparql_query_string =~ s/\n              /\n/gs;
	print $program_output $sparql_query_string;
	close($program_output);	
}

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($switches->get('error_file') eq "STDERR") {
	print "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
