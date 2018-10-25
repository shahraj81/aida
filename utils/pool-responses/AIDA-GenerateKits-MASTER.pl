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
#   (1) A single pooler output file, and
#   (2) The max number of elements to go in a single kit,
# and produces as output a set of kits as desired by LDC.
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
$switches->addVarSwitch('prefix', "Specify the prefix of the output kits");
$switches->put('prefix', "kits");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addVarSwitch('m', "How large can the kit be? This value is provided by LDC.");
$switches->put('m', "200");
$switches->addParam("pool", "required", "File containing pool");
$switches->addParam("output", "required", "Kits output directory");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

my $pool_filename = $switches->get("pool");
$logger->NIST_die("$pool_filename does not exist") unless -e $pool_filename;

my $output_dir = $switches->get("output");
$logger->NIST_die("$output_dir already exists")
		if(-e $output_dir);
system("mkdir $output_dir");

my $max_kit_size = $switches->get("m");
my $prefix = $switches->get("prefix");

my $pool = Pool->new($logger, $pool_filename);


my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors+$num_warnings) {
	foreach my $kb_id($pool->get("ALL_KEYS")) {
 		my $kit = $pool->get("BY_KEY", $kb_id);
 		my $total_entries = scalar($kit->toarray());
 		my $total_kits = ceil($total_entries/$max_kit_size);
 		my @kit_entries = $kit->toarray();
 		my $linenum = 0;
 		for(my $kit_num = 1; $kit_num <=$total_kits; $kit_num++){
 			my $output_filename = "$output_dir/kit_$kb_id\_$kit_num\_$total_kits\.tab";
 			open(my $program_output, ">:utf8", $output_filename) or $logger->NIST_die("Could not open $output_filename: $!");
 			for(my $i=($kit_num-1)*$max_kit_size; $i<$kit_num*$max_kit_size && $i<$total_entries; $i++) {
 				$linenum++;
 				my $output_line = $kit_entries[$i];
 				$output_line =~ s/<ID>/$linenum/;
 				print $program_output "$output_line\n";
 			}
 			close($program_output);
 		}
	}
}

unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;

