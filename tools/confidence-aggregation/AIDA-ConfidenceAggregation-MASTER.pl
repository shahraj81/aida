#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ConfidenceAggregationManagerLib;

### DO INCLUDE
##################################################################################### 
# This program implements default confidence aggregation for M18
#
# Author: Shahzad Rajput
# Please send questions or comments to shahzadrajput "at" gmail "dot" com
#
# For usage, run with no arguments
##################################################################################### 

my $version = "2019.0.0";

#####################################################################################
# Subroutines and support code
#####################################################################################

my $types_allowed = {
  TA1_CL => {
    NAME => 'TA1_CL',
    DESCRIPTION => "Input directory contains responses to task1 class queries",
    AGGREGATE_CONFIDENCE => sub {
      my ($logger, $input_file, $output_file) = @_;
      my $filehandler = FileHandler->new($logger, $input_file);
      my @entries = $filehandler->get("ENTRIES")->toarray();
      foreach my $entry(@entries) {
        $entry->set("?ag_cv", $entry->get("?t_cv") * $entry->get("?j_cv") * $entry->get("?cm_cv"))
      }
      open(my $program_output, ">:utf8", $output_file)
        or $logger->record_problem('MISSING_FILE', $output_file, $!);
      print $program_output $filehandler->get("HEADER")->get("LINE"), "\n";
      foreach my $entry(sort {$b->get("?ag_cv") <=> $a->get("?ag_cv")} @entries) {
        print $program_output $entry->get("LINE"), "\n";
      }
      close $program_output;
    },
  },
  TA1_GR => {
    NAME => 'TA1_GR',
    DESCRIPTION => "Input directory contains responses to task1 graph queries",
    AGGREGATE_CONFIDENCE => sub {
    },
  },
  TA2_ZH => {
    NAME => 'TA2_ZH',
    DESCRIPTION => "Input directory contains responses to task2 zerohop queries",
    AGGREGATE_CONFIDENCE => sub {
    },
  },
  TA2_GR => {
    NAME => 'TA2_GR',
    DESCRIPTION => "Input directory contains responses to task2 graph queries",
    AGGREGATE_CONFIDENCE => sub {
    },
  },
};

sub aggregate_confidences {
  my ($logger, $type, $input_file, $output_file) = @_;
  &{$types_allowed->{$type}{AGGREGATE_CONFIDENCE}}($logger, $input_file, $output_file);
}

#####################################################################################
# Runtime switches and main program
#####################################################################################

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Aggregate Confidences.",
  "type is one of the following:\n" . &main::build_documentation($types_allowed) .
                        "");

$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("type", "required", "Type of the input file (see below for options)");
$switches->addParam("input", "required", "Input directory containing one of more directories containing SPARQL query response files");
$switches->addParam("output", "required", "Specify an output directory.");
$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
my $error_output = $logger->get_error_output();

my $path;
foreach $path(($switches->get("input"))) {
  $logger->NIST_die("$path does not exist") unless -e $path;
}

foreach $path(($switches->get("output"))) {
  $logger->NIST_die("$path already exists") if -e $path;
}

my $input_dir = $switches->get("input");
my $output_dir = $switches->get("output");
my $type = $switches->get("type");

$logger->NIST_die("$input_dir is not a directory") unless -d $input_dir;
$logger->NIST_die("Unexpected value of type $type") unless $types_allowed->{$type};

system("mkdir -p " . $switches->get("output"));

foreach my $input_subdir (<$input_dir/*>) {
  # skip if not a directory
  next unless -d $input_subdir;

  # get subdirectory name
  my $subdir_name = $input_subdir;
  $subdir_name =~ s/^(.*?\/)+//g;

  # create output subdirectory
  my $output_subdir = "$output_dir/$subdir_name";
  print STDERR "-creating directory $output_subdir\n";
  system("mkdir -p $output_subdir");
    
  # iterate through all response files that match a pattern 
  # inside this subdirectory
  my $pattern = "$input_subdir/AIDA_$type\_";
  print STDERR "-looking for files like: $pattern*.rq.tsv\n";
  foreach my $input_file(<$pattern*.rq.tsv>) {
    my $filename = $input_file;
    $filename =~ s/^(.*?\/)+//g;
    print STDERR "-processing $input_file\n";
    
    my $output_file = "$output_subdir/$filename";
    print STDERR "-output: $output_file\n";
    
    # call the default aggregation function
    &aggregate_confidences($logger, $type, $input_file, $output_file);
  }
}

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($switches->get('error_file') eq "STDERR") {
  print "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
  print "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
