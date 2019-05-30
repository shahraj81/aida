#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ExtractSentenceBoundariesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program extracts sentence boundaries from LTF documents.
#
# Author: Shahzad Rajput
# Please send questions or comments to shahzadrajput "at" gmail "dot" com
#
# For usage, run with no arguments
##################################################################################### 

my $version = "2018.0.2";

# Filehandles for program and error output
my $program_output = *STDOUT{IO};
my $error_output = *STDERR{IO};

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Extract sentence boundaries",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("docid_mappings", "required", "DocumentID to DocumentElementID mappings");
$switches->addParam("ltf", "required", "Directory containing raw ltf files included in the corpus");
$switches->addParam("output", "required", "Output file");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("docid_mappings"),
					$switches->get("ltf"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

my $output_filename = $switches->get("output");
$logger->NIST_die("$output_filename already exists")
	if(-e $output_filename);

open($program_output, ">:utf8", $output_filename)
	or $logger->NIST_die("Could not open $output_filename: $!");

my $ltf_directory = $switches->get("ltf");
my $docid_mappings_file = $switches->get("docid_mappings");

my $docid_mappings = DocumentIDsMappings->new($logger, $docid_mappings_file);

my %sentence_boundaries;
foreach my $docid(sort $docid_mappings->get("DOCUMENTS")->get("ALL_KEYS")) {
	my @doceids = map {$_->get("DOCUMENTELEMENTID")} $docid_mappings->get("DOCUMENTS")->get("BY_KEY", $docid)->get("DOCUMENTELEMENTS")->toarray();
	foreach my $doceid(sort @doceids) { 
		my $filename = "$ltf_directory/$doceid.ltf.xml";
		unless(-e $filename) {
			$logger->record_debug_information("FILENOTFOUND", $filename, {FILENAME => __FILE__, LINENUM => __LINE__});
			next;
		}
		print STDERR "$filename\n";
		open(my $program_input, "<", $filename) or $logger->NIST_die("Could not open $filename");
		my ($running_offset, $start_segment_offset, $end_segment_offset, $segment_id, $start_char, $end_char) = (0,0,0,0,0,0);
		while(my $line = <$program_input>) {
			my $length = length($line);
			chomp $line;
			if($line =~ /^<SEG id="segment-(\d+)" start_char="(\d+)" end_char="(\d+)">$/){
				$start_segment_offset = $running_offset;
				($segment_id, $start_char, $end_char) = ($1, $2, $3);
			}
			if($line =~ /^<\/SEG>/) {
				$end_segment_offset = $running_offset + $length - 1;
				$sentence_boundaries{$doceid}{$segment_id} = 
					{ 
						START_CHAR => $start_char, 
						END_CHAR => $end_char,
						START_SEGMENT_OFFSET => $start_segment_offset,
						END_SEGMENT_OFFSET => $end_segment_offset,
					};
			}
			$running_offset += $length;
		}
		close($program_input);
	}
}

my ($num_errors, $num_warnings) = $logger->report_all_information();
unless($num_errors+$num_warnings) {
	print $program_output join("\t", ("doceid", "segment_id", "start_char", "end_char", "start_segment_offset", "end_segment_offset")), "\n";
	foreach my $doceid(sort keys %sentence_boundaries) {
		foreach my $segment_id(sort {$a<=>$b} keys %{$sentence_boundaries{$doceid}}) {
			my ($start_char, $end_char, $start_segment_offset, $end_segment_offset)
				= map {$sentence_boundaries{$doceid}{$segment_id}{$_}}
					qw(START_CHAR END_CHAR START_SEGMENT_OFFSET END_SEGMENT_OFFSET);
			print $program_output join("\t", ($doceid, $segment_id, $start_char, $end_char, $start_segment_offset, $end_segment_offset)), "\n";
		}
	}
}

unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No warnings encountered.\n" unless ($num_errors || $num_warnings);
}

print $error_output ($num_warnings || 'No'), " warning", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit 0;

# change log

# 2018.0.2: adding segment start and end offsets to the output
# 2018.0.1: sentence boundaries generated for all documents (and not limited to coredocs)
# 2018.0.0: original version
