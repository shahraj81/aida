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

### DO NOT INCLUDE
##################################################################################### 
# Library inclusions
##################################################################################### 
### DO INCLUDE
### DO INCLUDE Container              ConfidenceAggregationManagerLib.pm
### DO INCLUDE Entry                  ConfidenceAggregationManagerLib.pm
### DO INCLUDE FileHandler            ConfidenceAggregationManagerLib.pm
### DO INCLUDE Header                 ConfidenceAggregationManagerLib.pm
### DO INCLUDE Logger                 ConfidenceAggregationManagerLib.pm
### DO INCLUDE Super                  ConfidenceAggregationManagerLib.pm
### DO INCLUDE SuperObject            ConfidenceAggregationManagerLib.pm
### DO INCLUDE Switches               ConfidenceAggregationManagerLib.pm
### DO INCLUDE Utils                  ConfidenceAggregationManagerLib.pm

#####################################################################################
# Subroutines and support code
#####################################################################################

my $types_allowed = {
  TA1_CL => {
    NAME => 'TA1_CL',
    DESCRIPTION => "Input directory contains responses to task1 class queries",
    AGGREGATE_CONFIDENCE => sub {
      # the docker returns a ranking of all the entity clusters in the SPARQL output file.
      my ($logger, $input_file, $output_file, @ac_fields) = @_;
      my $filehandler = FileHandler->new($logger, $input_file);
      my @entries = $filehandler->get("ENTRIES")->toarray();
      my %clusters;
      # compute aggregate confidence
      foreach my $entry(@entries) {
        $logger->record_problem("MULTIPLE_ENTRIES_IN_A_CLUSTER", $entry->get("?cluster"), $entry->get("WHERE"))
          if($clusters{$entry->get("?cluster")});
        $entry->set("?ag_cv", &aggregate_confidence_value($entry, @ac_fields));
        $clusters{$entry->get("?cluster")} = $entry->get("?ag_cv");
      }
      open(my $program_output, ">:utf8", $output_file)
        or $logger->record_problem('MISSING_FILE', $output_file, $!);
      my $rank = 1;
      # print header
      print $program_output join("\t", ("cluster_id", "rank")), "\n";
      # print lines
      foreach my $cluster_id(sort {$clusters{$b}<=>$clusters{$a}} keys %clusters) {
        print $program_output join("\t", ($cluster_id, $rank)), "\n";
        $rank++;
      }
      close $program_output;
    },
    CONFIDENCE_AGGREGATION_FIELDS => [qw(?t_cv ?j_cv ?cm_cv)],
  },
  TA1_GR => {
    NAME => 'TA1_GR',
    DESCRIPTION => "Input directory contains responses to task1 graph queries",
    AGGREGATE_CONFIDENCE => sub {
      # The docker must output a file containing the same columns as the SPARQL output will, plus two additional columns
      # (rank and aggregate edge justification confidence value) appended at the end;
      # the docker output file must filter the contents of the SPARQL output file such that for each unique edge
      # (having unique combination of subject cluster ID, edge label, and object cluster ID), there is at most one line
      # in the docker output file.  NIST will sort the lines for the edges by rank and pool, assess, and score the only
      # those edges that have highest rank.  Each line must have a rank that is unique across the entire output file of
      # the docker.  Columns in the docker output file must be tab-separated (as in the SPARQL output file).
      #
      # By default, NIST will compute aggregate edge justification confidence (AEJC) as product of:
      #        ?oinf_j_cv    # confidence of object informativeJustification
      #        ?obcm_cv      # cluster membership confidence of the object
      #        ?edge_cv      # confidence of a compound justification for the argument assertion
      #        ?sbcm_cv      # cluster membership confidence of the subject
      my ($logger, $input_file, $output_file, @ac_fields) = @_;
      # Read the input file
      my $filehandler = FileHandler->new($logger, $input_file);
      my @entries = $filehandler->get("ENTRIES")->toarray();
      my %edges;
      foreach my $entry(@entries) {
        $entry->set("?ag_cv", &aggregate_confidence_value($entry, @ac_fields));
        my ($subject_cluster, $edge_type_q, $object_cluster, $confidence, $line) =
          map {$entry->get($_)} qw(?subject_cluster ?edge_type_q ?object_cluster ?ag_cv LINE);
        my $edge_str = "$subject_cluster-$edge_type_q-$object_cluster";
        $entry->set("EDGE", $edge_str);
        next if (exists $edges{$edge_str} && $confidence <= $edges{$edge_str}->get("?ag_cv"));
        $edges{$edge_str} = $entry;
      }
      open(my $program_output, ">:utf8", $output_file)
        or $logger->record_problem('MISSING_FILE', $output_file, $!);
      my $header = $filehandler->get("HEADER")->get("LINE");
      print $program_output join("\t", ($header, "?ag_cv", "?rank")), "\n";
      my $rank = 1;
      foreach my $edge_str(sort {$edges{$b}->get("?ag_cv") <=> $edges{$a}->get("?ag_cv")} keys %edges) {
        my $line = $edges{$edge_str}->get("LINE");
        my $ag_cv = $edges{$edge_str}->get("?ag_cv");
        print $program_output join("\t", ($line, $ag_cv, $rank)), "\n";
        $rank++;
      }
      close $program_output;
    },
    CONFIDENCE_AGGREGATION_FIELDS => [qw(?oinf_j_cv ?obcm_cv ?edge_cv ?sbcm_cv)],
  },
  TA2_ZH => {
    NAME => 'TA2_ZH',
    DESCRIPTION => "Input directory contains responses to task2 zerohop queries",
    AGGREGATE_CONFIDENCE => sub {
      # The docker must take a SPARQL output file and query entity KB ID, and must output a file containing a ranking of
      # all the entity clusters in the SPARQL output file.  The docker output file must contain two tab-delimited columns:
      #   • Column 1: entity cluster ID
      #   • Column 2: rank of entity cluster ID
      # For 2019, for each query, NIST will evaluate only the cluster with rank 1.
      #
      # NIST will provide a default docker that ranks an entity cluster according to the confidence of the aida:LinkAssertion
      # linking the cluster to the reference KB ID (see example zero-hop SQARQL query).  If two clusters have the same
      # aida:LinkAssertion confidence for the same reference KB ID, NIST will arbitrarily pick one cluster as having higher rank.
      # Therefore, it is the responsibility of participants to define the confidence of the aida:LinkAssertion in such a way that
      # distinguishes between clusters (or else optionally provide an alternative docker to rank the entity clusters).
      my ($logger, $input_file, $output_file, @ac_fields) = @_;
      my $filehandler = FileHandler->new($logger, $input_file);
      my @entries = $filehandler->get("ENTRIES")->toarray();
      my %clusters;
      # compute aggregate confidence
      foreach my $entry(@entries) {
        $entry->set("?ag_cv", &aggregate_confidence_value($entry, @ac_fields));
        next if exists $clusters{$entry->get("?cluster")} && $clusters{$entry->get("?cluster")} > $entry->get("?ag_cv");
        $clusters{$entry->get("?cluster")} = $entry->get("?ag_cv");
      }
      open(my $program_output, ">:utf8", $output_file)
        or $logger->record_problem('MISSING_FILE', $output_file, $!);
      my $rank = 1;
      # print header
      print $program_output join("\t", ("cluster_id", "rank")), "\n";
      # print lines
      foreach my $cluster_id(sort {$clusters{$b}<=>$clusters{$a}} keys %clusters) {
        print $program_output join("\t", ($cluster_id, $rank)), "\n";
        $rank++;
      }
      close $program_output;
    },
    CONFIDENCE_AGGREGATION_FIELDS => [qw(?link_cv)],
  },
  TA2_GR => {
    NAME => 'TA2_GR',
    DESCRIPTION => "Input directory contains responses to task2 graph queries",
    AGGREGATE_CONFIDENCE => sub {
      # The docker must rank the subject clusters and (for each cluster) filter possible assessment items to select k=1
      # assessment items for the cluster. The docker for TA2 graph queries must take a SPARQL output file, edge label, and
      # query entity KB ID.  The docker must output a file containing the same tab-delimited columns as the SPARQL output
      # fill, plus two additional columns (rank and aggregate edge justification confidence value) appended at the end of
      # each line; the docker output file must filter the contents of the SPARQL output file such that for each subject
      # cluster ID, there is at most k=1 line in the docker output file.  Each line in the docker output file must have a
      # rank that is unique across the entire output file of the docker
    },
  },
};

sub aggregate_confidences {
  my ($logger, $type, $input_file, $output_file) = @_;
  my @fields = @{$types_allowed->{$type}{CONFIDENCE_AGGREGATION_FIELDS}};
  &{$types_allowed->{$type}{AGGREGATE_CONFIDENCE}}($logger, $input_file, $output_file, @fields);
}

sub aggregate_confidence_value {
  my ($entry, @ac_fields) = @_;
  my $ag_cv = 1.0;
  foreach my $ac_field(@ac_fields) {
    $ag_cv *= $entry->get($ac_field);
  }
  $ag_cv;
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

system("mkdir -p " . $switches->get("output"));
foreach $path(($switches->get("output"))) {
  foreach my $subdir(<$path/*>) {
    $logger->NIST_die("$path is non-empty") if -e $path;
  }
}

my $input_dir = $switches->get("input");
my $output_dir = $switches->get("output");
my $type = $switches->get("type");

$logger->NIST_die("$input_dir is not a directory") unless -d $input_dir;
$logger->NIST_die("Unexpected value of type $type") unless $types_allowed->{$type};

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
