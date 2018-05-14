#!/usr/bin/perl
use strict;

use TranslateManagerLib;

my ($filename, $filehandler, $header, $entries, $i);

# Load parent children DOCID mapping from parent_children.tab
my $documents = Documents->new();
my $documentelements = DocumentElements->new();

$filename = "data/LDC2018E01_AIDA_Seedling_Corpus_V1/docs/parent_children.tab";
$filehandler = FileHandler->new($filename);
$header = $filehandler->get("HEADER");
$entries = $filehandler->get("ENTRIES");
$i=0;
foreach my $entry( $entries->toarray() ){
  $i++;
  #print "ENTRY # $i:\n", $entry->tostring(), "\n";
  my $document_id = $entry->get("parent_uid");
  my ($document_eid) = split(/\./, $entry->get("child_file"));
  my $detype = $entry->get("dtyp");
  
  my $document = $documents->get("BY_KEY", $document_id);
  $document->set("DOCUMENTID", $document_id);
  my $documentelement = DocumentElement->new();
  $documentelement->set("DOCUMENT", $document);
  $documentelement->set("DOCUMENTID", $document_id);
  $documentelement->set("DOCUMENTELEMENTID", $document_eid);
  $documentelement->set("TYPE", $detype);
  
  $document->add_document_element($documentelement);
  $documentelements->add($documentelement, $document_eid) unless $document_eid eq "n/a";
}

# Load parent children DOCID mapping from uid_info_v2.tab

$filename = "data/LDC2018E01_AIDA_Seedling_Corpus_V1/docs/uid_info_v2.tab";
$filehandler = FileHandler->new($filename);
$header = $filehandler->get("HEADER");
$entries = $filehandler->get("ENTRIES");
$i=0;
foreach my $entry( $entries->toarray() ){
  $i++;
  #print "ENTRY # $i:\n", $entry->tostring(), "\n";
  my $document_id = $entry->get("uid");
  my ($document_eid) = split(/\./, $entry->get("derived_uid"));
  
  my $document = $documents->get("BY_KEY", $document_id);
  $document->set("DOCUMENTID", $document_id);
  my $documentelement = DocumentElement->new();
  $documentelement->set("DOCUMENT", $document);
  $documentelement->set("DOCUMENTID", $document_id);
  $documentelement->set("DOCUMENTELEMENTID", $document_eid);
  
  $document->add_document_element($documentelement);
  $documentelements->add($documentelement, $document_eid) unless $document_eid eq "n/a";
}


#####################################################################################
# Print document and document-element mapping in RDF Turtle format
#####################################################################################

foreach my $document($documents->toarray()) {
	my $document_id = $document->get("DOCUMENTID");
	my $node_id = "D_$document_id";
	print "\n# Document $document_id and it's elements\n";
	print "aida:$node_id rdf:type aida:document ;\n";
  print "              rdf:ID \"$document_id\" ;\n";
  my @document_element_ids = map {"              aida:has_element aida:D_".$_}
                              map {$_->get("DOCUMENTELEMENTID")} 
                               $document->get("DOCUMENTELEMENTS")->toarray();
                               
  my $document_elements_rdf = join(" ;\n", @document_element_ids);
  print "$document_elements_rdf .\n";
}

foreach my $document_element($documentelements->toarray()) {
  my $document_element_id = $document_element->get("DOCUMENTELEMENTID");
  my $document_element_modality = $document_element->get("TYPE");
  my $document_id = $document_element->get("DOCUMENTID");
  my $node_id = "D_$document_element_id";
  print "\n# Document element $document_id and it's parent\n";
  print "aida:$node_id rdf:type aida:document_element ;\n";
  print "              rdf:ID \"$document_element_id\" ;\n";
  print "              aida:is_element_of aida:D_$document_id .\n";                               
  print "              aida:modality aida:$document_element_modality .\n";
}

#####################################################################################
# Process T101_ent_mentions.tab
#####################################################################################

$filename = "data/LDC2018E45_AIDA_Scenario_1_Seedling_Annotation_V2.0/data/T101/T101_ent_mentions.tab";
$filehandler = FileHandler->new($filename);
$header = $filehandler->get("HEADER");
$entries = $filehandler->get("ENTRIES"); 

# variable to hold entities
my $entities = Entities->new();
$i=0;
foreach my $entry( $entries->toarray() ){
	$i++;
	#print "ENTRY # $i:\n", $entry->tostring(), "\n";
	my $document_eid = $entry->get("provenance");
	my $document_id = $documentelements->get("BY_KEY", $document_eid)->get("DOCUMENTID") || undef;
	my $mention = Mention->new();
	my $span = Span->new(
	             $entry->get("provenance"),
	             $document_eid,
	             $entry->get("textoffset_startchar"),
	             $entry->get("textoffset_endchar"),
	         );
	my $justification = Justification->new();
	$justification->add_span($span);
	$mention->add_justification($justification);
  $mention->set("MENTIONID", $entry->get("entitymention_id"));
  $mention->set("TEXT_STRING", $entry->get("text_string"));
  $mention->set("JUSTIFICATION_STRING", $entry->get("justification"));
  $mention->set("TREEID", $entry->get("tree_id"));
  $mention->set("TYPE", $entry->get("type"));
	
	my $entity = $entities->get("BY_KEY", $entry->get("kb_id"));
	
  $entity->set("KBID", $entry->get("kb_id")) unless $entity->set("KBID");
	$entity->set("TYPE", $entry->get("type")) unless $entity->set("TYPE");
	$entity->add_mention($mention);
}

#foreach my $entity($entities->toarray()) {
#	&Super::dump_structure($entity, 'Entity');
#	print "Total mentions: ", scalar $entity->get("MENTIONS")->toarray(), "\n";
#	getc();
#}