# Validate Responses

Last updated: 10/5/2018

This document describes:

	1. Scripts and packages required for running the validator,
	2. Support files required for running the validator,
	3. How to use these script(s),
	4. Some additional notes
	
## Introduction

This tool validates the responses submitted for AIDA M9 evaluation. 

## Scripts and packages

The following scripts and packages are provided for running the validator:

	1. AIDA-ValidateResponse-MASTER.pl (v2018.0.0)
	2. ValidateResponsesManagerLib.pm
	
You would also need to install the following Perl modules in order to run the above script(s):

	1. JSON.pm
	
Please refer to http://www.cpan.org/modules/INSTALL.html for a guide on how to install a Perl module.

## Support files required for running the script(s)

In order to run the above script(s), the following files are required:

	1. docid_mappings: File containing DocumentID to DocumentElementID mappings. This file will be made available. NOTE: This file is available as LDC2018E62.parent_children.tsv from https://portal.nextcentury.com/owncloud/index.php/s/9VPG8OyYB8QTuPw.
	2. queries_dtd: DTD file corresponding to the XML file containing queries. This file will be made available.
	3. queries_xml: XML file containing queries. The query file(s) will made available.
	4. responses_dtd: DTD file corresponding to the XML file containing responses. This file will be made available.
	5. responses_xml: XML file containing responses. This is the file being validated.
	
## How to use these script(s)

The usage of the script(s) can be seen by running with option -h or without any argument. For record, the usage of these scripts is given below:

### Usage of AIDA-ValidateResponse-MASTER.pl

~~~
AIDA-ValidateResponses-MASTER.pl:  Validate XML response file

Usage: AIDA-ValidateResponses-MASTER.pl {-switch {-switch ...}} docid_mappings queries_dtd queries_xml responses_dtd responses_xml output

Legal switches are:
  -error_file <value>  Specify a file to which error output should be redirected
                         (Default = STDERR).
  -help                Show help
  -scope <value>       Specify the scope at which validation is to be performed.
                         (Default = anywhere).
  -version             Print version number and exit
parameters are:
  docid_mappings  DocumentID to DocumentElementID mappings (Required).
  queries_dtd     DTD file corresponding to the XML file containing queries
                    (Required).
  queries_xml     XML file containing queries (Required).
  responses_dtd   DTD file corresponding to the XML file containing response
                    (Required).
  responses_xml   XML file containing responses (Required).
  output          Validated responses file (Required).

-scope is one of the following:
  anywhere:     Justifications may come from anywhere.
  withincorpus: All justifications in a response file should come from a corpus document
  withindoc:    All justifications in a response file should come from a single corpus document
~~~

### Running the validator on TA1 response file

In order to validate a TA1 response file, you may run the following command:

~~~
perl AIDA-ValidateResponses-MASTER.pl -scope withindoc -error_file validate_responses.errlog docid_mappings.tsv queries.dtd queries.xml responses.dtd responses.xml valid_responses.xml
~~~

### Running the validator on TA2 response file

In order to validate a TA2 response file, you may run the following command:

~~~
perl AIDA-ValidateResponses-MASTER.pl -scope withincorpus -error_file validate_responses.errlog docid_mappings.tsv queries.dtd queries.xml responses.dtd responses.xml valid_responses.xml
~~~

### Some notes

- Teams are required to validate the `responses.xml` file required as input by the above script against the DTD provided by NIST.
- The file specified in place of `docid_mappings` is a tsv file that is originally from LDC but is modified by NIST. This file will be provided along with the query files. This file is available as LDC2018E62.parent_children.tsv from https://portal.nextcentury.com/owncloud/index.php/s/9VPG8OyYB8QTuPw.
- The above script(s) assume that the output file and error log file do not exist.
- The file specified in place of `queries_dtd` or `responses_dtd` must not have any comments in it. Again, this file will be provided along with the queries file. Six DTD files will be provided, which should not be renamed nor the content be changed without approval.

	1/2. class_[query|response].dtd
	3/4. zerohop_[query|response].dtd
	5/6. graph_[query|response].dtd
