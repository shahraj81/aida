#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use FixAssessmentsManagerLib;

### DO INCLUDE
##################################################################################### 
# This program explains why two ecs were merged into a group
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
my $reasons;
my $relation_ecs;
my $next_ec_num = 1000;

sub next_ec {
  my $next_ec = "NILR$next_ec_num";
  $next_ec_num++;
  $next_ec;
}

sub undo_normalize {
  my ($entry) = @_;
  my %undo_normalize = (CORRECT => "correct", INCORRECT => "wrong", YES => "yes", NO => "no");
  foreach my $key(qw(ASSESSMENT OBJECT_LINKABILITY PREDICATE_JUSTIFICATION_CORRECTNESS)) {
    my $value = $entry->get($key);
    if(defined $value && exists $undo_normalize{$value}) {
      $entry->set($key, $undo_normalize{$value});
    }
  }
}

sub relation_entry_to_ec {
  my ($entry, $arg1_assessment_entry, $arg2_assessment_entry) = @_;
  my $relation_type = $entry->get("RELATION_TYPE");
  my $arg1_label = $entry->get("ARG1_LABEL");
  my $arg2_label = $entry->get("ARG2_LABEL");
  my $arg1_ec = $arg1_assessment_entry->get("OBJECT_FQEC");
  my $arg2_ec = $arg2_assessment_entry->get("OBJECT_FQEC");
  my $key;
  if($arg1_label eq $arg2_label) {
    $key = $arg1_ec . "=" . $arg1_label . "_" . $relation_type . "_" . $arg2_label . "=" . $arg2_ec;
  }
  else {
    my $arg_ecs = {$arg1_label=>$arg1_ec, $arg2_label => $arg2_ec};
    my @labels = sort keys %{$arg_ecs};
    my @ecs = map {$arg_ecs->{$_}} @labels;
    $key = $ecs[0] . "=" . $labels[0] . "_" . $relation_type . "_" . $labels[1] . "=" . $ecs[1];
  }
  my $ec;
  if($relation_ecs->{$key}) {
    $ec = $relation_ecs->{$key};
  }
  else {
    $ec = next_ec();
    $relation_ecs->{$key} = $ec;
  }
  $ec;
}

sub get_global_equals_string {
  my ($global_equals, $input_ec_set) = @_;
  my %ecs;
  foreach my $ec(split(/\|/, $input_ec_set)) {
    $ecs{$ec} = 1;
    if($global_equals->{$ec}) {
      foreach my $set(keys %{$global_equals->{$ec}}) {
        foreach my $member(split(/\|/, $set)) {
          $ecs{$member} = 1;
        }
      }
    }
  }
  join("|", sort keys %ecs);
}

sub get_mention_info {
  my ($mentions, $object_justification) = @_;
  my %info;
  foreach my $mention_id(keys %{$mentions->{SPAN_TO_MENTIONIDS}{$object_justification}}) {
    foreach my $kb_id(keys %{$mentions->{MENTIONID_TO_KBIDS}{$mention_id}}) {
      $info{"MENTION_ID=$mention_id KB_ID=$kb_id"} = 1;
    }
  }
  "\n" . join("\n", sort keys %info);
}

sub get_ecs_from_object_jusification {
  my ($mentions, $object_justification) = @_;
  my %ecs;
  foreach my $mention_id(keys %{$mentions->{SPAN_TO_MENTIONIDS}{$object_justification}}) {
    foreach my $kb_id(keys %{$mentions->{MENTIONID_TO_KBIDS}{$mention_id}}) {
      my @ecs = split(/\|/, $kb_id);
      foreach my $ec(@ecs) {
        $ecs{$ec}{"$mention_id:$ec"} = 1;
      }
    }
  }
  if(scalar keys %ecs > 1) {
    foreach my $ec1(keys %ecs) {
      foreach my $ec2(keys %ecs) {
        my $ec1_mention_ids = join(",", keys %{$ecs{$ec1}});
        my $ec2_mention_ids = join(",", keys %{$ecs{$ec2}});
        my $reason = {OBJECT_JUSTIFICATION=>$object_justification,
                      EC1s=>$ec1_mention_ids,
                      EC2s=>$ec2_mention_ids};
        push(@{$reasons->{$ec1}{$ec2}}, $reason) unless $ec1 eq $ec2;
      }
    }
  }
  join("|", sort keys %ecs);
}

sub entry_to_key {
  my ($entry, $fields) = @_;
  join("::", map {$entry->get($_)} @$fields);
}

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Fix assessments",
                        "");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("ambiguous", "required", "tab version of duplicate_aug_entries_mapping.xlsx");
$switches->addParam("annotations", "required", "Directory containing annotation tab files");
$switches->addParam("input", "required", "Assessment package as receieved from LDC");
$switches->addParam("ECs", "required", "Comma-separated pair of ECs");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("ambiguous"),
                  $switches->get("annotations"),
                  $switches->get("input"))) {
  $logger->NIST_die("$path does not exist") unless -e $path;
}

my $global_equals_filename = $switches->get("ambiguous");
my $input_assessments_dir = $switches->get("input");
my @questioned_ecs = split(",", $switches->get("ECs"));

my $linenum;

# (1a) Load global equals
$linenum = 1;
my $global_equals;
open(FILE, $global_equals_filename);
while(my $line = <FILE>) {
  chomp $line;
  my @ecs = sort keys {map {$_=>1} split(/\|/, $line)};
  foreach my $ec1(@ecs) {
    $global_equals->{$ec1}{$line} = 1;
    foreach my $ec2(@ecs) {
      my $reason = {FILENAME=>$global_equals_filename, LINENUM=>$linenum, LINE=>$line};
      push(@{$reasons->{$ec1}{$ec2}}, $reason) unless $ec1 eq $ec2;
    }
  }
  $linenum++;
}
close(FILE);

# (1b) Go through annotation tab files and collect KBID from linking tab files for
# each entity span via entity mention span. 
#    - then collapse it with assessment package by adding pipe to object ECs

my $mentions;
my $annotations_dir = $switches->get("annotations");
foreach my $topic(<$annotations_dir/data/*>) {
  my (undef, $topic_id) = $topic =~ /(.*?\/)+(.*?)$/;
  my $arg_mentions_filename = "$annotations_dir/data/$topic_id/$topic_id\_arg_mentions.tab";
  foreach my $entry(FileHandler->new($logger, $arg_mentions_filename)->get("ENTRIES")->toarray()) {
    my $mention_id = $entry->get("argmention_id");
    my $document_id = $entry->get("root_uid");
    my $document_element_id = $entry->get("child_uid");
    my $textoffset_startchar = $entry->get("textoffset_startchar");
    my $textoffset_endchar = $entry->get("textoffset_endchar");
    my $keyframe_id = $entry->get("keyframe_id");
    my $mediamention_coordinates = $entry->get("mediamention_coordinates");
    next if $document_element_id eq "EMPTY_TBD";
    my $span;
    if($textoffset_startchar && $textoffset_endchar && $textoffset_startchar =~ /^\d+$/ && $textoffset_endchar =~ /^\d+$/ ) {
      $span = $document_id .
              ":" .
              $document_element_id .
              ":" .
              "(" . $textoffset_startchar . "," . "0" . ")" .
              "-" .
              "(" . $textoffset_endchar . "," . "0" . ")";
      $mentions->{MENTIONID_TO_SPANS}{$mention_id}{$span} = 1;
      $mentions->{SPAN_TO_MENTIONIDS}{$span}{$mention_id} = 1;
    }
    else {
      $document_element_id = $keyframe_id if $keyframe_id ne "EMPTY_NA";
      if($mediamention_coordinates =~ /^\d+,\d+,\d+,\d+$/) {
        my ($sx, $sy, $ex, $ey) = split(",", $mediamention_coordinates);
        $span = $document_id .
              ":" .
              $document_element_id .
              ":" .
              "(" . $sx . "," . $sy . ")" .
              "-" .
              "(" . $ex . "," . $ey . ")";
        $mentions->{MENTIONID_TO_SPANS}{$mention_id}{$span} = 1;
        $mentions->{SPAN_TO_MENTIONIDS}{$span}{$mention_id} = 1;
      }
    }
  }
  my $kb_linking_filename = "$annotations_dir/data/$topic_id/$topic_id\_kb_linking.tab";
  foreach my $entry(FileHandler->new($logger, $kb_linking_filename)->get("ENTRIES")->toarray()) {
    my $kb_id = $entry->get("kb_id");
    my $mention_id = $entry->get("mention_id");
    $mentions->{MENTIONID_TO_KBIDS}{$mention_id}{$kb_id} = 1;
#    The following is not desired, because in the context of the mention KB-IDs
#    are confusable but its not true globally
# 
#    # if kb_id is a list, add update global equals
#    if($kb_id =~ /\|/) {
#      my @ecs = sort keys {map {$_=>1} split(/\|/, $kb_id)};
#      foreach my $ec(@ecs) {
#        $global_equals->{$ec}{$kb_id} = 1;
#      }
#    }
  }
}

# (2) For each kit in assessment package merge ECs
my $input_assessments = Assessments->new($logger, $input_assessments_dir, "graph");
my %equals;
foreach my $entry($input_assessments->toarray()) {
  next unless ($entry->get("PREDICATE_JUSTIFICATION_CORRECTNESS") eq "CORRECT" && $entry->get("OBJECT_LINKABILITY") eq "YES");
  my ($filename, $linenum) = map {$entry->get("WHERE")->{$_}} qw(FILENAME LINENUM);
  my $predicate = $entry->get("PREDICATE");
  my $document_id = $entry->get("DOCUMENT_ID");
  my $object_justification = $entry->get("OBJECT_JUSTIFICATION");
  $object_justification = $document_id . ":" . $object_justification;
  my $ecs_from_annotation = get_ecs_from_object_jusification($mentions, $object_justification);
  my $ecs_string = $entry->get("OBJECT_FQEC");
  $ecs_string = $ecs_string . "|" . $ecs_from_annotation if $ecs_from_annotation;
  $ecs_string = get_global_equals_string($global_equals, $ecs_string);
  my @ecs = sort keys {map {$_=>1} split(/\|/, $ecs_string)};
  # If there is a generated ID as well as a manually assigned ID then prefer the manual one
  @ecs = grep {$_ !~ /^NILG\d+$/} @ecs
    if(scalar (grep {$_ =~ /^NILG\d+$/} @ecs) && scalar (grep {$_ !~ /^NILG\d+$/} @ecs));
  foreach my $ec1(@ecs) {
    foreach my $ec2(@ecs) {
      $equals{$predicate}{$ec1}{$ec2} = 1 if($ec1 ne $ec2);
      my $mention_info = get_mention_info($mentions, $object_justification);
      my $reason = {FILENAME=>$filename, 
                    LINENUM=>$linenum, 
                    ASSSESSMENT_LINE=>$entry->get("LINE"),
                    OBJECT_JUSTIFICATION=>$object_justification,
                    ECS_FROM_ANNOTAION=>$ecs_from_annotation,
                    OBJECT_FQEC_FROM_ASSESSMENT=>$entry->get("OBJECT_FQEC"),
                    MERGED_ECS_STRING=>$ecs_string,
                    MENTION_INFO_FROM_ANNOTATION=>$mention_info};
      push(@{$reasons->{$ec1}{$ec2}}, $reason) unless $ec1 eq $ec2;
    }
  }
}

restart:
foreach my $predicate(keys %equals) {
  foreach my $k1(keys %{$equals{$predicate}}) {
    foreach my $k2(keys %{$equals{$predicate}{$k1}}) {
      foreach my $k3(keys %{$equals{$predicate}{$k1}}) {
        next if $k2 eq $k3;
        unless(exists $equals{$predicate}{$k2}{$k3}) {
          $equals{$predicate}{$k2}{$k3} = 1;
          
          my $reason = {INFERENCE=>1,
                    PREDICATE=>$predicate,
                    K1 => $k1,
                    K2 => $k2,
                    K3 => $k3};
          push(@{$reasons->{$k2}{$k3}}, $reason) unless $k2 eq $k3;
          
          goto restart;
        }
      }
    }
  }
}

print "--Questioned ECs are: ", join(",", @questioned_ecs), "\n";
my ($ec1,$ec2) = @questioned_ecs;
if(exists $reasons->{$ec1}{$ec2}) {
  foreach my $reason(@{$reasons->{$ec1}{$ec2}}) {
    print "\n\n";
    foreach my $key(sort keys %$reason) {
      my $value = $reason->{$key};
      print "--$key = $value\n";
    }
  }
}
print "\n\n--changing order:\n";
if(exists $reasons->{$ec2}{$ec1}) {
  foreach my $reason(@{$reasons->{$ec2}{$ec1}}) {
    print "\n\n";
    foreach my $key(sort keys %$reason) {
      my $value = $reason->{$key};
      print "--$key = $value\n";
    }
  }
}

#my ($num_errors, $num_warnings) = $logger->report_all_information();
#
#unless($switches->get('error_file') eq "STDERR") {
#  print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
#  print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
#}
#
#print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;