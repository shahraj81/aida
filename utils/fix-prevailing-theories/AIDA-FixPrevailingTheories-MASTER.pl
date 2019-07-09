#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use FixPrevailingTheoriesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program takes LDCs prevailing theory files in NIST modified flattened format, 
# and a file containing kbid and the replace-with value with which the kbid will be 
# replaced with.
#
# Author: Shahzad Rajput
# Please send questions or comments to shahzadrajput "at" gmail "dot" com
#
# For usage, run with no arguments
##################################################################################### 

my $version = "2019.0.0";

# Filehandles for program and error output
my $program_output = *STDOUT{IO};
my $error_output = *STDERR{IO};

# Validation code
my $validation_retval = 0;

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Patch prevailing theories",
                        "");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("correctionfile", "required", "file containing kbid and the replace-with value with which the kbid will be replaced with");
$switches->addParam("input", "required", "Input directory containing original flattened prevailing theory files.");
$switches->addParam("output", "required", "Output directory containing corrected flattened prevailing theory files.");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("correctionfile"),
          $switches->get("input"))) {
  $logger->NIST_die("$path does not exist") unless -e $path;
}

foreach my $path(($switches->get("output"))) {
  $logger->NIST_die("$path alreay exist") if -e $path;
}

my $input_dir = $switches->get("input");
my $output_dir = $switches->get("output");
my $correction_file = $switches->get("correctionfile");

my $correction_container = Container->new($logger);
foreach my $entry(FileHandler->new($logger, $correction_file)->get("ENTRIES")->toarray()) {
  my $kbid = $entry->get("orig_kb_id");
  my $replace_with = $entry->get("replace_with");
  $correction_container->add($replace_with, $kbid);
}

system("mkdir $output_dir");

foreach my $input_file(<$input_dir/*.tab>) {
  my $filename = $input_file;
  $filename =~ s/^(.*?\/)+//g;
  my $output_file = "$output_dir/$filename";
  print "--processing: $input_file\n";
  print "--output: $output_file\n";
  open(my $program_output, ">:utf8", $output_file)
     or $logger->NIST_die("Could not open $output_file for output");
  my $filehandler = FileHandler->new($logger, $input_file);
  print $program_output $filehandler->get("HEADER")->get("LINE"), "\n";
  foreach my $entry($filehandler->get("ENTRIES")->toarray()) {
    my $kbid = $entry->get("Argument KB ID");
    my $line = $entry->get("LINE");
    if($correction_container->exists($kbid)) {
      my $replace_with = $correction_container->get("BY_KEY", $kbid);
      $entry->{MAP}{"Argument KB ID"} = $replace_with;
      my @elements = map {$entry->{MAP}{$_}} @{$entry->get("HEADER")->get("ELEMENTS")};
      $line = join("\t", @elements);
    }
    print $program_output "$line\n";
  }
  close($program_output);
}

my ($num_errors, $num_warnings) = $logger->report_all_information();

$validation_retval = $logger->get_error_code() if($num_errors+$num_warnings);

unless($switches->get('error_file') eq "STDERR") {
  print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
  print STDERR "No problems encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " problem", ($num_warnings == 1 ? '' : 's'), " encountered.\n";

exit $validation_retval;

# Revision history

## 2019.0.0: original version