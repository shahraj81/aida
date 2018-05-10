#!/usr/bin/perl
use strict;

use TranslateManagerLib;

my $filename = "data/LDC2018E45_AIDA_Scenario_1_Seedling_Annotation_V2.0/data/T101/T101_ent_mentions.tab";
my $entity_mentions_fh = FileHandler->new($filename);

# display
# $entity_mentions_fh->display();

# get header
my $header = $entity_mentions_fh->get("HEADER");

# get entries
my $entries = $entity_mentions_fh->get("ENTRIES"); 
my $num_of_entries = $entries->get("NUM_OF_ENTRIES");

for(my $i=0; $i<$num_of_entries; $i++){
	print "ENTRY # $i:\n";
	print $entries->get("ENTRY_AT", $i)->tostring();
	print "\n";
}

