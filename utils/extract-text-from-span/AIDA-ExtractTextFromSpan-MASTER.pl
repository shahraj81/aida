#!/usr/bin/perl

use warnings;
use strict;

#binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ExtractTextFromSpanManagerLib;
use Storable;

### DO INCLUDE
##################################################################################### 
# This program takes as input: 
#   (1) path of the LTF files,
#   (2) a sentence boundaries file, and
#   (3) text span, 
# and displays the text string corresponding to the span as output.
#
# Author: Shahzad Rajput
# Please send questions or comments to shahzadrajput "at" gmail "dot" com
#
# For usage, run with no arguments
##################################################################################### 

my $version = "2018.0.1";

# Filehandles for program and error output
my $program_output = *STDOUT{IO};
my $error_output = *STDERR{IO};

# Validation code
my $validation_retval = 0;

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Get text string from span",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addParam("ltf", "required", "Path to LTF files");
$switches->addParam("cache", "required", "Path to cache; if it exists the cache will be used, otherwise it will be created");
$switches->addParam("sentence_boundaries", "required", "File containing sentence boundaries");
$switches->addParam("span", "required", "The input span");

$switches->process(@ARGV);

my $logger = Logger->new();
my $error_filename = $switches->get("error_file");
$logger->set_error_output($error_filename);
$error_output = $logger->get_error_output();

foreach my $path(($switches->get("ltf"), 
					$switches->get("sentence_boundaries"))) {
	$logger->NIST_die("$path does not exist") unless -e $path;
}

my $pathname = $switches->get("ltf");
my $sentence_boundaries_filename = $switches->get("sentence_boundaries");
my $span = $switches->get("span");
my ($doceid, $start, $end) = $span =~ /^(.*?):(\d+)-(\d+)$/;
my $filename = "$pathname/$doceid\.ltf.xml";
my $span_string = "NIL";

my $cache_dir = $switches->get("cache");
system "mkdir $cache_dir" unless(-e $cache_dir);
my $cache_filename = "$cache_dir/cache.bin";
my $sentence_boundaries;
unless(-e $cache_filename) {
	$sentence_boundaries = SentenceBoundaries->new($logger, $sentence_boundaries_filename);
	$sentence_boundaries->remove_logger();
	store $sentence_boundaries, $cache_filename;
}
else {
	$sentence_boundaries = retrieve $cache_filename;	
	$logger->NIST_die("Unable to retrieve from $cache_filename!\n") unless defined $sentence_boundaries;
}
$sentence_boundaries->add_logger($logger);

my $segment = $sentence_boundaries->get("BOUNDARY", "$doceid:($start,0)-($end,0)");
if($segment) {
	my $segment_start = $segment->get("START_SEGMENT");
	my $segment_text = "";
	open(my $input_file, "<:utf8", $filename) or $logger->NIST_die("Could not open file $filename");
	seek($input_file, $segment_start, 0);
	while(my $line = <$input_file>) {
		$segment_text .= "$line";
		last if $line =~ /<\/SEG>/;
	}
	close($input_file);
	
	my ($original_text) = $segment_text =~ /<ORIGINAL_TEXT>(.*?)<\/ORIGINAL_TEXT>/;
	my $sentence_start_char = $segment->get("START_CHAR");
	$start = $start - $sentence_start_char;
	$end = $end - $sentence_start_char;
	my $length = $end-$start+1;
	$span_string = substr($original_text, $start, $length);
}

my ($num_errors, $num_warnings) = $logger->report_all_information();
$validation_retval = $Logger::NIST_error_code if($num_errors+$num_warnings);
print "$span_string\n" unless($num_errors);
unless($switches->get('error_file') eq "STDERR") {
	print STDERR "Problems encountered (warnings: $num_warnings, errors: $num_errors)\n" if ($num_errors || $num_warnings);
	print STDERR "No problems encountered.\n" unless ($num_errors || $num_warnings);
}
print $error_output ($num_warnings || 'No'), " problems", ($num_warnings == 1 ? '' : 's'), " encountered.\n";
exit $validation_retval;