#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ValidateResponsesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program validates SPARQL output files.
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
my $switches = SwitchProcessor->new($0, "Validate SPARQL output files",
                        "");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addConstantSwitch('no_error_code', 'false', "Do not return any error code if problems are encountered?");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("docid_mappings", "required", "LDC2019*.parent_children.tsv file containing DocumentID to DocumentElementID mappings");
$switches->addParam("sentence_boundaries", "required", "File containing sentence boundaries");
$switches->addParam("images_boundingboxes", "required", "File containing image bounding boxes");
$switches->addParam("keyframes_boundingboxes", "required", "File containing keyframe bounding boxes");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("coredocs", "required", "File containing ids of core documents (responses from outside coredocs will be removed)");
$switches->addParam("run_id", "required", "Run ID");
$switches->addParam("input", "required", "Run directory containing SPARQL output files");
$switches->addParam("output", "required", "Specify a directory to which validated output should be written");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("docid_mappings"), 
          $switches->get("sentence_boundaries"),
          $switches->get("images_boundingboxes"),
          $switches->get("keyframes_boundingboxes"),
          $switches->get("queries_dtd"),
          $switches->get("queries_xml"),
          $switches->get("coredocs"),
          $switches->get("input"))) {
  $logger->NIST_die("$path does not exist") unless -e $path;
}

my $input_dir = $switches->get("input");
$logger->NIST_die("path $input_dir exists but it is not a directory")
  unless (-d $input_dir);

my $output_dir = $switches->get("output");
system("mkdir -p $output_dir");

my $docid_mappings_filename = $switches->get("docid_mappings");
my $sentence_boundaries_filename = $switches->get("sentence_boundaries");
my $images_boundingboxes_filename = $switches->get("images_boundingboxes");
my $keyframes_boundingboxes_filename = $switches->get("keyframes_boundingboxes");
my $coredocs_filename = $switches->get("coredocs");
my $run_id = $switches->get("run_id");

my $coredocs = CoreDocs->new($logger, $coredocs_filename);
my $docid_mappings = DocumentIDsMappings->new($logger, $docid_mappings_filename, $coredocs);
my $text_document_boundaries = TextDocumentBoundaries->new($logger, $sentence_boundaries_filename);
my $images_boundingboxes = ImagesBoundingBoxes->new($logger, $images_boundingboxes_filename);
my $keyframes_boundingboxes = KeyFramesBoundingBoxes->new($logger, $keyframes_boundingboxes_filename);

my $queries = QuerySet->new($logger, $switches->get("queries_dtd"), $switches->get("queries_xml"));

my @response_files;
foreach my $input_subdir (<$input_dir/*>) {
  # skip if not a directory
  next unless -d $input_subdir;
  # iterate through all response files
  foreach my $input_file(<$input_subdir/*.rq.tsv>) {
    my $query_id = $input_file;
    $query_id =~ s/^(.*?\/)+//g;
    $query_id =~ s/\.rq\.tsv//;
    unless ($queries->exists($query_id)) {
      $logger->record_debug_information("SKIPPING_INPUT_FILE", $input_file, {FILENAME => __FILE__, LINENUM => __LINE__});
      next;
    }
    print STDERR "--file $input_file added to the process queue\n";
    push(@response_files, $input_file);
  }
}

# create a ResponseSet object
my $responses = ResponseSet->new($logger,
                  $queries, 
                  $docid_mappings, 
                  $text_document_boundaries, 
                  $images_boundingboxes, 
                  $keyframes_boundingboxes,
                  $run_id,
                  @response_files);

# write the validated responses to the directory maintaining the input directory structure
$responses->write_valid_output($output_dir);

my ($num_errors, $num_warnings) = $logger->report_all_information();

$validation_retval = $logger->get_error_code() if(!$switches->get("no_error_code") && $num_errors+$num_warnings);

unless($switches->get('error_file') eq "STDERR") {
  print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
  print STDERR "No problems encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " problem", ($num_warnings == 1 ? '' : 's'), " encountered.\n";

exit $validation_retval;