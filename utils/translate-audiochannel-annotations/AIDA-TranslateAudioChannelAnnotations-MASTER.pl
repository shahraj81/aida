#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use TranslationManagerLib;

### DO INCLUDE
##################################################################################### 
# This program takes LDCs annotation files in their original form, and adds keyframe 
# ID to the entries that contain information from the audio channel.
#
# Author: Shahzad Rajput
# Please send questions or comments to shahzadrajput "at" gmail "dot" com
#
# For usage, run with no arguments
##################################################################################### 

my $version = "2019.0.1";

# Filehandles for program and error output
my $program_output = *STDOUT{IO};
my $error_output = *STDERR{IO};

# Validation code
my $validation_retval = 0;

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Translate annotations",
                        "");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addConstantSwitch("replace", "true", "Replace `sound` to `picture`?");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("msbfile", "required", "masterShotBoundary.msb");
$switches->addParam("keyframes_boundingboxes", "required", "File containing keyframe bounding boxes");
$switches->addParam("input", "required", "Input annotations directory");
$switches->addParam("output", "required", "Output directory");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("msbfile"), 
          $switches->get("keyframes_boundingboxes"),
          $switches->get("input"))) {
  $logger->NIST_die("$path does not exist") unless -e $path;
}

my $input_dir = $switches->get("input");
$logger->NIST_die("path $input_dir exists but it is not a directory")
  unless (-d $input_dir);

my $output_dir = $switches->get("output");
$logger->NIST_die("$output_dir already exists") if -e $output_dir;
system("mkdir -p $output_dir");

my $replace_flag = $switches->get("replace");
my $keyframes_boundingboxes_filename = $switches->get("keyframes_boundingboxes");
my $keyframes_boundingboxes = KeyFramesBoundingBoxes->new($logger, $keyframes_boundingboxes_filename);
my $msb_filename = $switches->get("msbfile");
my %msb_map;
my %keyframenum_to_keyframeid;
foreach my $entry(FileHandler->new($logger, $msb_filename)->get("ENTRIES")->toarray()) {
  my $keyframe_id = $entry->get("keyframe_id");
  my ($doceid, $shot_num) = split("_", $keyframe_id);
  my $start_time = $entry->get("start_time");
  my $end_time = $entry->get("end_time");
  my $keyframe_num = $entry->get("keyframe_num");
  $logger->NIST_die("STARTTIME $start_time already exists for $doceid")
    if $msb_map{$doceid}{$start_time};
  $msb_map{$doceid}{$start_time} = {SHOTNUM => $shot_num, END_TIME => $end_time};
  $keyframenum_to_keyframeid{$keyframe_num} = $keyframe_id;
}

foreach my $input_subdir (<$input_dir/*>) {
  # skip if not a directory
  next unless -d $input_subdir;
  # iterate through all response files
  my @elements = split(/\//, $input_subdir);
  my $subdir_name = pop @elements;
  my $output_dir = "$output_dir/$subdir_name";
  system("mkdir -p $output_dir");
  foreach my $input_file(<$input_subdir/R*.tab>) {
    my $filename = $input_file;
    $filename =~ s/^(.*?\/)+//g;
    my $output_file = "$output_dir/$filename";
    open(my $program_output, ">:utf8", $output_file)
      or $logger->NIST_die("Could not open $output_file for output");
    my $filehandler = FileHandler->new($logger, $input_file);
    my $header = $filehandler->get("HEADER");
    print $program_output $header->get("LINE"), "\n";
    my @entries = $filehandler->get("ENTRIES")->toarray();
    foreach my $entry(@entries) {
      my $signal_type = $entry->get("mediamention_signaltype");
      if($signal_type eq "sound") {
        my $shot_num;
        my $mention_start_time = $entry->get("mediamention_starttime");
        my $doceid = $entry->get("child_uid");
        foreach my $keyframe_start_time(sort {$a <=> $b} keys %{$msb_map{$doceid}}) {
          if($mention_start_time >= $keyframe_start_time) {
            $shot_num = $msb_map{$doceid}{$keyframe_start_time}{SHOTNUM};
          }
        }
        my $keyframe_id = "$doceid\_$shot_num";
        my $keyframe_boundary = $keyframes_boundingboxes->get("BY_KEY", $keyframe_id);
        my ($top_left_x, $top_left_y, $bottom_right_x, $bottom_right_y)
          = map {$keyframe_boundary->get($_)} qw(TOP_LEFT_X TOP_LEFT_Y BOTTOM_RIGHT_X BOTTOM_RIGHT_Y);
        $entry->{MAP}{keyframe_id} = $keyframe_id;
        $entry->{MAP}{mediamention_signaltype} = "picture" if $replace_flag;
        $entry->{MAP}{mediamention_coordinates} = "$top_left_x,$top_left_y,$bottom_right_x,$bottom_right_y";
      }
      
      my @values;
      foreach my $key(@{$header->get("ELEMENTS")}) {
        my $value = $entry->get($key);
        push(@values, $value);
      }
      my $line = join("\t", @values);
      print $program_output $line, "\n";
    }
    close($program_output);
  }
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
## 2019.0.1: replace switch added to control replacing the string `sound` with `picture`