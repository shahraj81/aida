# Resolve Queries

Last updated: 10/1/2018

This document describes:

	1. Scripts and packages required for applying SPARQL queries to the knowledge base,
	2. Support files required for running the script(s), and
	3. How to use these script(s).

## Introduction

This tool supports application of SPARQL queries to a knowledge base in AIF format in order to produce output in the simplified xml response format.

## Scripts and packages

The following scripts and packages are provided for applying SPARQL queries against the knowledge base:

	1. AIDA-ResolveQueries-MASTER.pl (v2018.0.0)
	2. ResolveQueriesManagerLib.pm

You would also need to install the following Perl modules in order to run the above script(s):

	1. JSON.pm

Please refer to http://www.cpan.org/modules/INSTALL.html for a guide on how to install a Perl module. 

## Support files required for running the script(s)

## How to use these script(s)

### Usage of AIDA-ResolveQueries-MASTER.pl

~~~
AIDA-ResolveQueries-MASTER.pl:  Apply a set of SPARQL evaluation queries to a
                                knowledge base in Turtle RDF format to produce
                                AIDA output for assessment.

Usage: AIDA-ResolveQueries-MASTER.pl {-switch {-switch ...}} docid_mappings queries_dtd queries_xml input intermediate output

Legal switches are:
  -error_file <value>  Specify a file to which error output should be redirected
                         (Default = STDERR).
  -help                Show help
  -sparql <value>      Specify path to SPARQL executable (Default = sparql).
  -version             Print version number and exit
parameters are:
  docid_mappings  DocumentID to DocumentElementID mappings (Required).
  queries_dtd     DTD file corresponding to the XML file containing queries
                    (Required).
  queries_xml     XML file containing queries (Required).
  input           File containing the KB (for TA2 system) or directory
                    containing KBs (for TA1 system). (Required).
  intermediate    Specify a directory to be used for storing intermediate files.
                    (Required).
  output          Specify an output directory. (Required).
~~~
