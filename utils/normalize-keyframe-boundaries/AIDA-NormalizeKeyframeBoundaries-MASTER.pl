#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use NormalizeKeyframeBoundariesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program normalizes keyframe boundary file obtained from TRECVID team.
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

##################################################################################### 
# Subroutines
##################################################################################### 

sub compare {
  my ($a_doceid, $a_keyframenum) = split("_", $a);
  my ($b_doceid, $b_keyframenum) = split("_", $b);
  return $a_doceid cmp $b_doceid || 
          $a_keyframenum <=> $b_keyframenum;
}

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Normalize keyframe boundaries",
                        "");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("raw", "required", "Raw keyframes.width.height file");
$switches->addParam("mastershotboundary", "required", "masterShotBoundary.msb file");
$switches->addParam("output", "required", "Output file");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("raw"),
          $switches->get("mastershotboundary"))) {
  $logger->NIST_die("$path does not exist") unless -e $path;
}

my $output_filename = $switches->get("output");
$logger->NIST_die("$output_filename already exists")
  if(-e $output_filename);
open($program_output, ">:utf8", $output_filename)
  or $logger->NIST_die("Could not open $output_filename: $!");

my $input_file = $switches->get("raw");
my $msb_file = $switches->get("mastershotboundary");

my %videoid_to_doceid;
foreach my $entry(FileHandler->new($logger, $msb_file)->get("ENTRIES")->toarray()) {
  my $video_id = $entry->get("video_id");
  my $keyframe_id = $entry->get("keyframe_id");
  my ($doceid) = split("_", $keyframe_id);
  $logger->NIST_die("multiple doceids mapped to $video_id")
    if(exists $videoid_to_doceid{$video_id} && $videoid_to_doceid{$video_id} ne $doceid);
  $videoid_to_doceid{$video_id} = $doceid;
}

my %keyframeid_to_wxh;
foreach my $entry(FileHandler->new($logger, $input_file)->get("ENTRIES")->toarray()) {
  my $line = $entry->get("LINE");
  my $filename = $entry->get("filename");
  my $wxh = $entry->get("wxh");
  my ($video_id, $keyframe_num) = $filename =~ /^(v_.*?)_(\d+)\..*?$/;
  $logger->NIST_die("Missing map entry for $video_id") unless $videoid_to_doceid{$video_id};
  my $doceid = $videoid_to_doceid{$video_id};
  my $keyframe_id = "$doceid\_$keyframe_num";
  $logger->NIST_die("multiple wxh mapped to $keyframe_id")
    if(exists $keyframeid_to_wxh{$keyframe_id} && $keyframeid_to_wxh{$keyframe_id} ne $wxh);
  $keyframeid_to_wxh{$keyframe_id} = $wxh;
}

print $program_output join("\t", ("keyframe_id", "wxh")), "\n";
foreach my $keyframe_id(sort compare keys %keyframeid_to_wxh) {
  my $wxh = $keyframeid_to_wxh{$keyframe_id};
  print $program_output join("\t", ($keyframe_id, $wxh)), "\n";
}

close($program_output);

my ($num_errors, $num_warnings) = $logger->report_all_information();

unless($switches->get('error_file') eq "STDERR") {
  print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
  print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;

# change log

# 2019.0.0: original version
