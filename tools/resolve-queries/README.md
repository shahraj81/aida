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

In order to run SPARQL queries you may need to install Apache Jena. Please refer to https://jena.apache.org for downloading Apache Jena. 

## Support files required for running the script(s)

In order to run the above script(s), the following files are required:

	1. docid_mappings: File containing DocumentID to DocumentElementID mappings. This file will be made available.
	2. queries_dtd: DTD file corresponding to the XML file containing queries. This file will be made available.
	3. queries_xml: XML file containing queries. The query file(s) will made available.

## How to use these script(s)

The usage of the script(s) can be seen by running with option -h or without any argument. For record, the usage of these scripts is given below:

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

### Applying SPARQL queries

In order to apply SPARQL queries to a knowledge base, you may run the following command:

~~~
perl AIDA-ResolveQueries-MASTER.pl -error_file rq.errlog -sparql /path/to/sparql_executable docids_mappings.tsv queries.dtd queries.xml kbs/ intermediate/ output/
~~~

### Using the tool on example data

This tool comes with example data, including both example input and expected output, to demonstrate the usage. Example data can be found in the example directory with input, output and intermediate data directories:

	- input: aida/tools/resolve-queries/example/input
	- intermediate: aida/tools/resolve-queries/example/intermediate
	- output: aida/tools/resolve-queries/example/output

Note that the runs on all: class queries, zerohop queries and graph queries, and therefore produces the corresponding output in the respective subdirectories.

#### Input and output

In

#### Execution of the code on example data

In order to run the code on example data, you may run the following command:

~~~
make clean
make all
~~~

### Some notes

- Teams are recommended to validate output produced by the above script(s) against the DTD provided by NIST.
- The file specified in place of `docid_mappings` is a tsv file that is originally from LDC but is modified by NIST. This file will be provided along with the queries.
- The above script(s) assume that the intermediate data directory and the output directory does not exist.
- The file specified in place of `queries_dtd` must not have any comments in it. Again, this file will be provided along with the queries file. Three DTD files will be provided:
	1. class_query.dtd
	2. graph_query.dtd
	3. zerohop_query.dtd
These files should not be renamed nor the content be changed without approval.
- In the next few days, NIST is going to work with NCC in order to provide the teams with a docker to make it easy for them to run this tool without having to install dependencies individually.
