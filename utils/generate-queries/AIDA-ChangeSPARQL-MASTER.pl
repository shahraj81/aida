#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use GenerateQueriesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program reads in a SPARQL query XML file along with corresponding DTD file and
# produces a revised SPARQL query XML file as output where the revisions are made in
# SPARQL construct. Other parts of the XML including QUERYID, etc. stay the same.
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
my $switches = SwitchProcessor->new($0, "Update SPARQL Query XML file.",
                        "");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("output", "required", "Specify an output XML queries file containing revised SPARQL.");

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

my $output_filename = $switches->get("output");
open(my $program_output, ">:utf8", $output_filename)
  or $logger->record_problem('MISSING_FILE', $output_filename, $!);

my %templates = (
  TA1_CL => sub { return QueryGenerator::get_TA1_CLASS_SPARQL_QUERY_TEMPLATE(); },
  TA1_GR => sub { return QueryGenerator::get_TA1_GRAPH_SPARQL_QUERY_TEMPLATE(); },
  TA2_ZH => sub { return QueryGenerator::get_TA2_ZEROHOP_SPARQL_QUERY_TEMPLATE(); },
  TA2_GR => sub { return QueryGenerator::get_TA2_GRAPH_SPARQL_QUERY_TEMPLATE(); },
);

my %instances = (
  TA1_CL => sub {
              my ($query) = @_;
              my $query_id = $query->get("QUERYID");
              my $query_type = $query->get("ENTTYPE");
              my $sparql = &{$templates{TA1_CL}}();
              $sparql =~ s/\[__QUERY_ID__\]/$query_id/gs;
              $sparql =~ s/\[__TYPE__\]/$query_type/gs;
              $sparql;
            },
  TA1_GR => sub {
              my ($query) = @_;
              my $query_id = $query->get("QUERYID");
              my $edge_label = $query->get("PREDICATE");
              my $sparql = &{$templates{TA1_GR}}();
              $sparql =~ s/\[__QUERY_ID__\]/$query_id/gs;
              $sparql =~ s/\[__PREDICATE__\]/$edge_label/gs;
              $sparql;
            },
  TA2_ZH => sub {
              my ($query) = @_;
              my $query_id = $query->get("QUERYID");
              my $query_reference_kbid = $query->get("REFERENCE_KBID");
              my $sparql = &{$templates{TA2_ZH}}();
              $sparql =~ s/\[__QUERY_ID__\]/$query_id/gs;
              $sparql =~ s/\[__KBID__\]/$query_reference_kbid/gs;
              $sparql;
            },
  TA2_GR => sub {
              my ($query) = @_;
              my $query_id = $query->get("QUERYID");
              my $edge_label = $query->get("PREDICATE");
              my $query_reference_kbid = $query->get("REFERENCE_KBID");
              my $sparql = &{$templates{TA2_GR}}();
              $sparql =~ s/\[__QUERY_ID__\]/$query_id/gs;
              $sparql =~ s/\[__PREDICATE__\]/$edge_label/gs;
              $sparql =~ s/\[__KBID__\]/$query_reference_kbid/gs;
              $sparql;
            },
);

my $queries = QuerySet->new($logger, $switches->get("queries_dtd"), $switches->get("queries_xml"));
$queries->load();
foreach my $query($queries->get("QUERIES")->toarray()) {
  my $query_id = $query->get("QUERYID");
  my ($task_and_type_code) = $query_id =~ /AIDA_(TA\d\_..)\_/;
  my $new_sparql = &{$instances{$task_and_type_code}}($query);
  $query->get("XML_OBJECT")->get("CHILD", "sparql")->set("ELEMENT", $new_sparql);
}

print $program_output $queries->tostring();
close($program_output); 

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($switches->get('error_file') eq "STDERR") {
  print "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
  print "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;
