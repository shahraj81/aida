# Validate Responses

Last updated: 10/17/2018

This document describes:

	1. Scripts and packages required for running the validator,
	2. Support files required for running the validator,
	3. How to use these script(s),
	4. Some additional notes
	5. Revision history
	
## Introduction

This tool validates the responses submitted for AIDA M9 evaluation. 

## Scripts and packages

The following scripts and packages are provided for running the validator:

	1. AIDA-ValidateResponse-MASTER.pl (v2018.0.2)
	2. ValidateResponsesManagerLib.pm
	
You would also need to install the following Perl modules in order to run the above script(s):

	1. JSON.pm
	
Please refer to http://www.cpan.org/modules/INSTALL.html for a guide on how to install a Perl module.

## Support files required for running the script(s)

In order to run the above script(s), the following files are required:

	1. docid_mappings: File containing DocumentID to DocumentElementID mappings. This file will be made available as `LDC2018E62.parent_children.tsv`.
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
~~~

### Running the validator on TA1 response file

In order to validate a TA1 response file, you may run the following command:

~~~
perl AIDA-ValidateResponses-MASTER.pl -error_file validate_responses.errlog docid_mappings.tsv queries.dtd queries.xml responses.dtd responses.xml valid_responses.xml
~~~

### Running the validator on TA2 response file

In order to validate a TA2 response file, you may run the following command:

~~~
perl AIDA-ValidateResponses-MASTER.pl -error_file validate_responses.errlog docid_mappings.tsv queries.dtd queries.xml responses.dtd responses.xml valid_responses.xml
~~~

### Revision history

#### v2018.0.2:
- Scope does not need to be specified explicitly therefore switch -scope has been removed; In the new version, scope is internally inferred from the filename of the response file being validated. If the filename is TA2.[class|zerohop|graph]_responses.xml `withincorpus` scope is used and if the filename is DOCID.[class|zerohop|graph]_responses.xml `withindoc` scope is internally used.
- Validator generated false alarm when in a class query response it saw justification span from document elements belonging to multiple parents. (Thank you Hans for reporting the issue).
- Validator has been expanded to check if the justification type (TEXT, IMAGE, VIDEO) matches document element type (bmp, ltf, mp4, etc.).

#### v2018.0.1:
- The validator crashed without proper error message when an unexpected edgeid was provided. (Thank you Ryan for reporting the problem).

#### v2018.0.0:
- Original version

### Some notes

- Teams are required to validate the `responses.xml` file required as input by the above script against the DTD provided by NIST.
- The file specified in place of `docid_mappings` is a tsv file that is originally from LDC but is modified by NIST. This file will be provided along with the query files.
- The above script(s) assume that the output file and error log file do not exist.
- The file specified in place of `queries_dtd` or `responses_dtd` must not have any comments in it. Again, this file will be provided along with the queries file. Six DTD files will be provided, which should not be renamed nor the content be changed without approval.

	1/2. class_[query|response].dtd
	3/4. zerohop_[query|response].dtd
	5/6. graph_[query|response].dtd
