#!/usr/bin/perl -w
use strict;
use List::Util qw(shuffle);

my $M = 5;
my $N = 100;

# Rules for selecting coredocs
## 1. Include all tracer documents from 2019/input/tracer_docs.tab
## 2. Include M=5 documents per topic per language from all topic relevant documents 2019/input/doc_lang_topic.tab
## 3. Include remaining k documents from LDC2019E42.coredocs-all.txt minus all topic relevant documents from 2019/input/doc_lang_topic.tab, 
##    such that the total from (1), (2) and (3) is N

my $header;

my %tags;
my %selected;
# load tracer docs
my %tracer;
open(FILE, "2019/input/tracer_docs.tab");
$header = <FILE>;
while(my $line = <FILE>) {
  chomp $line;
  my ($rootid, $language, $topic) = split(/\t/, $line);
  $tracer{$rootid} = 1;
  $selected{$rootid} = {LANGUAGE=>$language, TOPIC=>$topic};
  $tags{$rootid}{TOPICS}{$topic} = 1;
  $tags{$rootid}{LANGUAGES}{$language} = 1;
}
close(FILE);


# select M=5 documents per topic per language from all topic relevant documents 2019/input/doc_lang_topic.tab
my %topicrel;
my %reldocs;
open(FILE, "2019/input/doc_lang_topic.tab");
$header = <FILE>;
while(my $line = <FILE>) {
  chomp $line;
  my ($treeid, $rootid, $language, $topic) = split(/\t/, $line);
  $tags{$rootid}{TOPICS}{$topic} = 1;
  $tags{$rootid}{LANGUAGES}{$language} = 1;
  $topicrel{$topic}{$language}{ALL}{$rootid} = 1;
  $reldocs{$rootid} = 1;
}

foreach my $topic(keys %topicrel) {
  foreach my $language(keys %{$topicrel{$topic}}) {
    my @docids = keys %{$topicrel{$topic}{$language}{ALL}};
    my @shuffled_docids = shuffle(@docids);
    foreach my $rootid(@shuffled_docids) {
      last if scalar keys %{$topicrel{$topic}{$language}{SELECTED}} == $M;
      next if $selected{$rootid};
      $topicrel{$topic}{$language}{SELECTED}{$rootid} = 1;
      $selected{$rootid} = 1;
    }
  }
}


# select the nonrelevant documents
my %nonreldocs;
open(FILE, "2019/input/LDC2019E42.coredocs-all.txt");
$header = <FILE>;
while(my $line = <FILE>) {
  chomp $line;
  my $rootid = $line;
  $nonreldocs{$rootid} = 1 unless $reldocs{$rootid};
}

my @nonreldocids = keys %nonreldocs;

my @shuffled_nonreldocids = shuffle(@nonreldocids);
foreach my $rootid(@shuffled_nonreldocids) {
  last if scalar keys %selected == $N;
  $selected{$rootid} = 1 unless $selected{$rootid};
}

open(my $program_output, ">2019/output/coredocs-$N.tab");
print $program_output "root_id\ttopics\tlanguages\ttracer\n";
foreach my $rootid(sort keys %selected) {
  my $tracer = "TRACER=NO";
  $tracer = "TRACER=YES" if $tracer{$rootid};
  my $topics = "NONE";
  my $languages = "NOTKNOWN";
  $topics = join(",", sort keys %{$tags{$rootid}{TOPICS}}) if $tags{$rootid}{TOPICS};
  $languages = join(",", sort keys %{$tags{$rootid}{LANGUAGES}}) if $tags{$rootid}{LANGUAGES};
  print $program_output join("\t", ($rootid, $topics, $languages, $tracer)), "\n";
}
close($program_output);