#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ScoreManagerLib;

### DO INCLUDE
##################################################################################### 
# This program scores responses against the QREL.
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
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Score SPARQL-based output files",
                        "");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addVarSwitch('runid', "Run ID of the system being scored");
$switches->put('runid', "system");
$switches->addParam("coredocs", "required", "List of core documents to be included in the pool");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
$switches->addParam("sentence_boundaries", "required", "File containing sentence boundaries");
$switches->addParam("images_boundingboxes", "required", "File containing image bounding boxes");
$switches->addParam("keyframes_boundingboxes", "required", "File containing keyframe bounding boxes");
$switches->addParam("queries", "required", "File containing queryids to be pooled.");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("salient_edges", "required", "File containing edges sailent to prevailing theories or 'none'");
$switches->addParam("assessments", "required", "Assessment package as receieved from LDC");
$switches->addParam("rundir", "required", "Run directory containing validated SPARQL output files");
$switches->addParam("cadir", "required", "Directory containing confidence aggregation output");
$switches->addParam("intermediate", "required", "Specify a directory where intermediate data can be written; the directory should not exist");
$switches->addParam("output", "required", "Output file");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("coredocs"),
          $switches->get("docid_mappings"),
          $switches->get("sentence_boundaries"),
          $switches->get("images_boundingboxes"),
          $switches->get("keyframes_boundingboxes"),
          $switches->get("queries"),
          $switches->get("queries_dtd"),
          $switches->get("queries_xml"),
          $switches->get("assessments"),
          $switches->get("rundir"),
          $switches->get("cadir"))) {
  $logger->NIST_die("$path does not exist") unless -e $path;
}

foreach my $path(($switches->get("salient_edges"))) {
  next if $path eq "none";
  $logger->NIST_die("$path does not exist") unless -e $path;
}

my $output_filename;
my $intermediate_dir = $switches->get("intermediate");
my $rundir_root = "$intermediate_dir/SPARQL-VALID-output";
my $cadir_root = "$intermediate_dir/SPARQL-CA-output";
my $runs_to_score_filename = "$intermediate_dir/runid.txt";
my $runid = $switches->get("runid");

$logger->NIST_die("$intermediate_dir already exists") if -e $intermediate_dir;
system("mkdir -p $rundir_root");
system("mkdir -p $cadir_root");
system("cp -r " . $switches->get("rundir") . " $rundir_root/$runid");
system("cp -r " . $switches->get("cadir") . " $cadir_root/$runid");
open($output_filename, ">$runs_to_score_filename");
print $output_filename "run_id\n$runid\n";
close($output_filename);

$output_filename = $switches->get("output");
$logger->NIST_die("$output_filename already exists") if -e $output_filename;
open($program_output, ">:utf8", $output_filename)
  or $logger->NIST_die("Could not open $output_filename: $!");

my $docid_mappings = DocumentIDsMappings->new($logger, $switches->get("docid_mappings"), CoreDocs->new($logger, $switches->get("coredocs")));
my $text_document_boundaries = TextDocumentBoundaries->new($logger, $switches->get("sentence_boundaries"));
my $images_boundingboxes = ImagesBoundingBoxes->new($logger, $switches->get("images_boundingboxes"));
my $keyframes_boundingboxes = KeyFramesBoundingBoxes->new($logger, $switches->get("keyframes_boundingboxes"));
my $queries = QuerySet->new($logger, $switches->get("queries_dtd"), $switches->get("queries_xml"));
my $queries_to_score = Container->new($logger);
map {$queries_to_score->add($_, $_->get("query_id"))}
      FileHandler->new($logger, $switches->get("queries"))->get("ENTRIES")->toarray();
my $runs_to_score = Container->new($logger);
map {$runs_to_score->add("KEY", $_->get("run_id"))}
      FileHandler->new($logger, $runs_to_score_filename)->get("ENTRIES")->toarray();
my $assessments = Assessments->new($logger, $switches->get("assessments"), $queries->get("QUERYTYPE"));
my $salient_edges = SalientEdges->new($logger, $switches->get("salient_edges"));

my $responses = ResponseSet->new($logger,
                      $queries,
                      $docid_mappings,
                      $text_document_boundaries,
                      $images_boundingboxes,
                      $keyframes_boundingboxes,
                      $rundir_root,
                      $runs_to_score,
                      $queries_to_score,
                      $cadir_root);

my $scorer = ScoresManager->new($logger, $runid, $docid_mappings, $queries, $salient_edges, $responses, $assessments, $queries_to_score);

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors) {
  print $program_output $scorer->print_lines($program_output);
}
close($program_output);

unless($switches->get('error_file') eq "STDERR") {
  print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
  print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;