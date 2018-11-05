#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use PoolResponsesManagerLib;
use POSIX;

### DO INCLUDE
##################################################################################### 
# This program takes as input: 
#   (1) the assessed kits
# and produces a QREl file to be used by the Scorer.
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
my $switches = SwitchProcessor->new($0, "Generate kits from the single pool file for LDC",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("type", "required", "legal choices: class, zerohop, graph");
$switches->addParam("boundaries", "required", "File containing sentence boundaries");
$switches->addParam("kits", "required", "Assessed kits directory");
$switches->addParam("output", "required", "the output QREL file");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

my $boundaries_filename = $switches->get("boundaries");
$logger->NIST_die("$boundaries_filename does not exist") unless -e $boundaries_filename;

my $kits_dir = $switches->get("kits");
$logger->NIST_die("$kits_dir does not exist") unless -e $kits_dir;

my $output_filename = $switches->get("output");
$logger->NIST_die("$output_filename already exists")
		if(-e $output_filename);
open($program_output, ">:utf8", $output_filename)
	or $logger->NIST_die("Could not open $output_filename: $!");
	
my %legal_types = map {$_=>1} qw(class zerohop graph);
my $type = $switches->get("type");
$logger->NIST_die("$type is not a legal value for type") 
	unless($legal_types{$type});

my $sentence_boundaries = SentenceBoundaries->new($logger, $boundaries_filename);
my $assessments = Assessments->new($logger, $kits_dir, $sentence_boundaries, $type);

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors+$num_warnings) {
	print $program_output $assessments->tostring();
}

unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
