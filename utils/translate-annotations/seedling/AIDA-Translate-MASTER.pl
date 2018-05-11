#!/usr/bin/perl
use strict;

use TranslateManagerLib;
#use Inheritance;
#
#my $gc = grandchild->new();
#$gc->get();
#
#exit;

my $filename = "data/LDC2018E45_AIDA_Scenario_1_Seedling_Annotation_V2.0/data/T101/T101_ent_mentions.tab";
my $entity_mentions_fh = FileHandler->new($filename);

# display
# $entity_mentions_fh->display();

# get header
my $header = $entity_mentions_fh->get("HEADER");

# get entries
my $entries = $entity_mentions_fh->get("ENTRIES"); 

# variable to hold entities
my $entities = Entities->new();

my $i=0;
foreach my $entry( $entries->toarray() ){
	$i++;
	print "ENTRY # $i:\n", $entry->tostring(), "\n";
	my $mention = Mention->new();
	my $span = Span->new(
	             $entry->get("provenance"),
	             undef,
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
	
	#&Super::dump_structure($entity, 'Entity');
	#getc();
}

foreach my $entity($entities->toarray()) {
	&Super::dump_structure($entity, 'Entity');
	print "Total mentions: ", scalar $entity->get("MENTIONS")->toarray(), "\n";
	#getc();
}