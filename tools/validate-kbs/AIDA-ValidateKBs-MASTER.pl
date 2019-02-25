#!/usr/bin/perl

use warnings;
use strict;

#binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ValidateKBsManagerLib;

### DO INCLUDE
##################################################################################### 
# This program takes as input: 
#   (1) path to test-case SPARQL queries,
#   (2) the KB file, and
# checks if the KB is valid for further processing.
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

# Validation code
my $validation_retval = 0;

# Constants and globals

my %testcases = (
		'MULTITYPE_MULTICONFIDENCE' => {
			PROBLEM => "KB_MULTITYPE_MULTICONFIDENCE",
			QUERY => "MULTITYPE_MULTICONFIDENCE.rq",
			EXPECTED_NUM_OUTPUT_LINES => 1,
		},
	);

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Validate the KB",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addParam("intermediate", "required", "Intermediate data directory");
$switches->addParam("testcases", "required", "Path to SPARQL queries corresponding to various test cases");
$switches->addParam("kb", "required", "The KB to be validated");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("testcases"),
					$switches->get("intermediate"),
					$switches->get("kb"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

my $intermediate_dir = $switches->get("intermediate");
my $pathname = $switches->get("testcases");
my $kb_filename = $switches->get("kb");
my (undef, $kb_name) = $kb_filename =~ /^(.*?\/)+(.*?)$/;
foreach my $dir(($intermediate_dir, $pathname)) {
	$dir =~ s/\/$//;
}

foreach my $testcase(keys %testcases) {
	my $query_filename = "$pathname/" . $testcases{$testcase}->{QUERY};
	my $output_filename = "$intermediate_dir/$kb_name";
	my $cmd = "sparql --data=$kb_filename --query=$query_filename --results=tsv > $output_filename";
	system($cmd);
	my $actual_num_output_lines = `wc -l < $output_filename`;
	$actual_num_output_lines =~ s/\s//g;
	if($actual_num_output_lines > $testcases{$testcase}->{EXPECTED_NUM_OUTPUT_LINES}) {
		$logger->record_problem($testcases{$testcase}->{PROBLEM}, {FILENAME=>$kb_filename, LINENUM=>"N/A"});
	}
}

my ($num_errors, $num_warnings) = $logger->report_all_information();
$validation_retval = $Logger::NIST_error_code if($num_errors+$num_warnings);
unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No problems encountered.\n" unless ($num_errors || $num_warnings);
}
print $error_output ($num_warnings || 'No'), " problems", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit $validation_retval;