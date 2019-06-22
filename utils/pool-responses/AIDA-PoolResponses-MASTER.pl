#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use PoolResponsesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program generate a pool of SPARQL output files for assessment
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
my $switches = SwitchProcessor->new($0, "Pool SPARQL output files",
                        "");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("depth", "required", "Parameter to control depth of responses to be included");
$switches->addParam("coredocs", "required", "List of core documents to be included in the pool");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
$switches->addParam("sentence_boundaries", "required", "File containing sentence boundaries");
$switches->addParam("images_boundingboxes", "required", "File containing image bounding boxes");
$switches->addParam("keyframes_boundingboxes", "required", "File containing keyframe bounding boxes");
$switches->addParam("queries", "required", "File containing queryids to be pooled.");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("rundir", "required", "Run directory containing SPARQL output files");
$switches->addParam("cadir", "required", "Directory containing confidence aggregation output");
$switches->addParam("input", "required", "File containing runs to be included in the pool");
$switches->addParam("previous_pool", "required", "Previous pooler output file (or an empty file)");
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
          $switches->get("rundir"),
          $switches->get("cadir"),
          $switches->get("input"),
          $switches->get("previous_pool"))) {
  $logger->NIST_die("$path does not exist") unless -e $path;
}

my $output_filename = $switches->get("output");
$logger->NIST_die("$output_filename already exists") if -e $output_filename;
open($program_output, ">:utf8", $output_filename)
	or $logger->NIST_die("Could not open $output_filename: $!");

my $depth = $switches->get("depth");
my $coredocs_filename = $switches->get("coredocs");
my $docid_mappings_filename = $switches->get("docid_mappings");
my $sentence_boundaries_filename = $switches->get("sentence_boundaries");
my $images_boundingboxes_filename = $switches->get("images_boundingboxes");
my $keyframes_boundingboxes_filename = $switches->get("keyframes_boundingboxes");
my $coredocs = CoreDocs->new($logger, $coredocs_filename);
my $previous_pool = Pool->new($logger, $switches->get("previous_pool"));
my $docid_mappings = DocumentIDsMappings->new($logger, $docid_mappings_filename, $coredocs);
my $text_document_boundaries = TextDocumentBoundaries->new($logger, $sentence_boundaries_filename);
my $images_boundingboxes = ImagesBoundingBoxes->new($logger, $images_boundingboxes_filename);
my $keyframes_boundingboxes = KeyFramesBoundingBoxes->new($logger, $keyframes_boundingboxes_filename);
my $queries = QuerySet->new($logger, $switches->get("queries_dtd"), $switches->get("queries_xml"));
my $queries_to_pool = Container->new($logger);
map {$queries_to_pool->add("KEY", $_->get("query_id"))}
      FileHandler->new($logger, $switches->get("queries"))->get("ENTRIES")->toarray();
my $runs_to_pool = Container->new($logger);
map {$runs_to_pool->add("KEY", $_->get("runid"))}
      FileHandler->new($logger, $switches->get("input"))->get("ENTRIES")->toarray();
my $rundir_root = $switches->get("rundir");
my $cadir_root = $switches->get("cadir");

my $pool = ResponsesPool->new(
             $logger, 
             $docid_mappings, 
             $text_document_boundaries, 
             $images_boundingboxes, 
             $keyframes_boundingboxes,
             $previous_pool,
             $depth,
             $coredocs,
             $queries, 
             $queries_to_pool,
             $runs_to_pool,
             $rundir_root, 
             $cadir_root);

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors+$num_warnings) {
  print $program_output $pool->tostring();
}

unless($switches->get('error_file') eq "STDERR") {
  print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
  print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;