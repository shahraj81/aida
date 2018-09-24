#!/usr/bin/perl

use warnings;
use strict;

binmode(STDOUT, ":utf8");

### DO NOT INCLUDE
use ResolveQueriesManagerLib;

### DO INCLUDE
##################################################################################### 
# This program validates applies AIDA queries to KBs in order to generate
# submissions. It takes as input the evaluation queries, a directory containing
# KBs split across TTL files in case of a TA1 submission, and a output directory. 
# In case of a TA2 systems, the submission is in the form of a single TTL file. 
#
# Author: Shahzad Rajput
# Please send questions or comments to shahzadrajput "at" gmail "dot" com
#
# For usage, run with no arguments
##################################################################################### 

my $version = "2018.0.0";

# Filehandles for program and error output
my $program_output = *STDOUT{IO};
my $error_output = *STDERR{IO};

##################################################################################### 
# Runtime switches and main program
##################################################################################### 

# Handle run-time switches
my $switches = SwitchProcessor->new($0, "Apply a set of SPARQL evaluation queries to a knowledge base \
											in Turtle RDF format to produce AIDA output for assessment.",
				    						"");
$switches->addHelpSwitch("help", "Show help");
$switches->addHelpSwitch("h", undef);
$switches->addVarSwitch('error_file', "Specify a file to which error output should be redirected");
$switches->put('error_file', "STDERR");
$switches->addVarSwitch('sparql', "Specify path to SPARQL executable");
$switches->put('sparql', "sparql");
$switches->addImmediateSwitch('version', sub { print "$0 version $version\n"; exit 0; }, "Print version number and exit");
$switches->addParam("queries_dtd", "required", "DTD file corresponding to the XML file containing queries");
$switches->addParam("queries_xml", "required", "XML file containing queries");
$switches->addParam("input", "required", "File containing the KB (for TA2 system) or directory containing KBs (for TA1 system).");
$switches->addParam("intermediate", "required", "Specify a directory to be used for storing intermediate files.");
$switches->addParam("output", "required", "Specify an output directory.");

$switches->process(@ARGV);
