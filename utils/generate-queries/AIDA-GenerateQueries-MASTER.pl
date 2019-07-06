#!/usr/bin/perl
use strict;

use GenerateQueriesManagerLib;

my $logger = Logger->new();
my $error_filename = "problems.log";
$logger->set_error_output($error_filename);
my $error_output = $logger->get_error_output();

my $data_type = "evaluation";
my %data_type_topic_and_pt_ids = (
      practice => [qw(R103_PT001 R103_PT002 R103_PT003 R103_PT004 R103_PT005 R105_PT001 R105_PT002 R107_PT001 R107_PT002)],
      evaluation => [qw(E101_PT001 E101_PT002 E101_PT003 E101_PT004 E101_PT005 E101_PT006 E101_PT007
                        E102_PT001 E102_PT002 E102_PT003 E102_PT004 E102_PT005
                        E103_PT001 E103_PT002 E103_PT003)],
   );
my %ref_kbid_prefixes = (
      practice => "LDC2019E44",
      evaluation => "LDC2019E43",
   );
my @topic_and_pt_ids = @{$data_type_topic_and_pt_ids{$data_type}};
my $ref_kbid_prefix = $ref_kbid_prefixes{$data_type};

my $dtd_files = Container->new("String");
$dtd_files->add("2019/input/queries_dtd/class_query.dtd", "class_query");
$dtd_files->add("2019/input/queries_dtd/zerohop_query.dtd", "zerohop_query");
$dtd_files->add("2019/input/queries_dtd/graph_query.dtd", "graph_query");

my $ontology_files = Container->new("String");
$ontology_files->add("2019/input/ontology/LDC_AIDAAnnotationOntologyWithMapping_V8_entities.tab", "entities");
$ontology_files->add("2019/input/ontology/LDC_AIDAAnnotationOntologyWithMapping_V8_events.tab", "events");
$ontology_files->add("2019/input/ontology/LDC_AIDAAnnotationOntologyWithMapping_V8_relations.tab", "relations");

my $prevailingtheory_files = Container->new("String");
map {$prevailingtheory_files->add("2019/input/prevailing-theories-$data_type/$_.tab", $_)}
  @topic_and_pt_ids;

my $named_refkbids_file = "2019/input/prevailing-theories-$data_type/named_refkb_nodes.txt";

my $parameters = Parameters->new($logger);
$parameters->set("ONTOLOGY_FILES", $ontology_files);
$parameters->set("PREVAILING_THEORY_FILES", $prevailingtheory_files);
$parameters->set("NAMED_REFKBIDS_FILENAME", $named_refkbids_file);
$parameters->set("DTD_FILES", $dtd_files);
$parameters->set("OUTPUT_DIR", "2019/output");
$parameters->set("ERRORLOG_FILE", $error_filename);
$parameters->set("TA1_CLASS_QUERYID_PREFIX", "AIDA_TA1_CL_2019");
$parameters->set("TA1_GRAPH_QUERYID_PREFIX", "AIDA_TA1_GR_2019");
$parameters->set("TA2_ZEROHOP_QUERYID_PREFIX", "AIDA_TA2_ZH_2019");
$parameters->set("TA2_GRAPH_QUERYID_PREFIX", "AIDA_TA2_GR_2019");
$parameters->set("REFERENCE_KBID_PREFIX", $ref_kbid_prefix);
$parameters->set("TA2_GRAPH_QUERY_MAPPINGS_FILENAME", "TA2_GraphQuery_mappings.txt");

$logger->NIST_die("Output directory exists") if -d $parameters->get("OUTPUT_DIR");

my $query_generator = QueryGenerator->new($logger, $parameters);

my $year = "2019";
foreach my $topic_and_pt_id(@topic_and_pt_ids) {
	my ($topic_id, $pt_id) = split("_", $topic_and_pt_id);
	$query_generator->generate_queries($year, $topic_id, $pt_id);
}

# output the mapping file for TA2_GRAPH_QUERIES 
my $output_mapping_filename = $parameters->get("OUTPUT_DIR") . "/" . $parameters->get("TA2_GRAPH_QUERY_MAPPINGS_FILENAME");
open(my $mapping_output, ">:utf8", $output_mapping_filename)
        or $logger->NIST_die("Could not open $output_mapping_filename: $!");
print $mapping_output "query_id\tevent_or_relation_kbid\n";
my @queries = $query_generator->get("TA2_GRAPH_QUERIES")->get("QUERIES")->toarray();
foreach my $query(@queries) {
  my $query_id = $query->get("QUERYID");
  foreach my $event_or_relation_kbid($query->get("EVENT_OR_RELATION_KBIDS")->toarray()) {
    print $mapping_output "$query_id\t$event_or_relation_kbid\n";
  }
}
close($mapping_output);

my ($num_errors, $num_warnings) = $logger->report_all_information();
print "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
print "No problems encountered.\n" unless ($num_errors || $num_warnings);
print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered\n";
exit 0;
