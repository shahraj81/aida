# Validate Responses

Last updated: 8/14/2019

This document describes:

	1. Scripts and packages required for running the validator,
	2. Support files required for running the validator,
	3. How to use these script(s),
	4. What is the validator checking for?
	5. Some additional notes,
	6. Revision history
	
## Introduction

This tool validates the output of SPARQL queries when applied using the NIST SPARQL query application docker. NOTE that the validator expects the output of the docker to be unchanged.

## Scripts and packages

The following scripts and packages are provided for running the validator:

	1. AIDA-ValidateResponse-MASTER.pl (v2019.0.2)
	2. ValidateResponsesManagerLib.pm
	
You would also need to install the following Perl modules in order to run the above script(s):

	1. JSON.pm
	
Please refer to http://www.cpan.org/modules/INSTALL.html for a guide on how to install a Perl module.

## Support files required for running the script(s)

In order to run the above script(s), the following files are required:

	1. docid_mappings: File containing DocumentID to DocumentElementID mappings (`LDC2018E62.parent_children.tsv`). This file will be provided.
	2. queries_dtd: DTD file corresponding to the XML file containing queries. This file will be provided.
	3. queries_xml: XML file containing queries. The query file(s) will be provided.
	4. sentence_boundaries: File containing sentence boundary information for all LTF files in the corpus. This file will be provided.
	5. images_boundingboxes: File containing sizes of all image files in the corpus. This file will be provided.
	6. keyframes_boundingboxes: File containing sizes of all keyframe image sizes for all video shots. This file will be provided.
	7. coredocs: File containing a subset of document IDs. Responses from these documents will be validated.
	8. run_id: Run ID.
	9. input: Run directory containing SPARQL output files as produced by the NIST SPARQL query application docker
	10. output: Directory where validated output is to be written.
	
### Usage of AIDA-ValidateResponse-MASTER.pl

The usage of the script(s) can be seen by running with option -h or without any argument. For record, the usage of these scripts is given below:

~~~
AIDA-ValidateResponses-MASTER.pl:  Validate SPARQL output files

Usage: AIDA-ValidateResponses-MASTER.pl {-switch {-switch ...}} docid_mappings sentence_boundaries images_boundingboxes keyframes_boundingboxes queries_dtd queries_xml coredocs run_id input output

Legal switches are:
  -error_file <value>  Specify a file to which error output should be redirected
                         (Default = STDERR).
  -help                Show help
  -no_error_code       Do not return any error code if problems are encountered?
  -version             Print version number and exit
parameters are:
  docid_mappings           LDC2019*.parent_children.tsv file containing
                             DocumentID to DocumentElementID mappings
                             (Required).
  sentence_boundaries      File containing sentence boundaries (Required).
  images_boundingboxes     File containing image bounding boxes (Required).
  keyframes_boundingboxes  File containing keyframe bounding boxes (Required).
  queries_dtd              DTD file corresponding to the XML file containing
                             queries (Required).
  queries_xml              XML file containing queries (Required).
  coredocs                 File containing ids of core documents (responses from
                             outside coredocs will be removed) (Required).
  run_id                   Run ID (Required).
  input                    Run directory containing SPARQL output files
                             (Required).
  output                   Specify a directory to which validated output should
                             be written (Required).
~~~

### How to run the validator?

In order to validate responses in a run directory, you may run the following command:

~~~
perl AIDA-ValidateResponses-MASTER.pl parent_children.tsv sentence_boundaries.txt image_boundaries.txt keyframe_boundaries.txt queries.dtd queries.xml coredocs.txt runname inputdir outputdir
~~~

### What is the validator checking for?

The validator is checking if:
  1. the document (i.e. the parent document) belongs to the corpus,
  2. the document element (i.e the child document) in the provenance (a) belongs to the corpus, and (b) is the child of the (parent) document,
  3. a single response in from the same document,
  4. confidence value is a number between (0,1],
  5. importance value is a number (or NULL for task3 graph response),
  6. Edge justification can be NULL for task3 graph responses,
  7. Text provenances are within the boundary of text document element,
  8. Image provenances are not outside the image boundary,
  9. Keyframe ID should a valid one,
  10. type of the entity should match one in the query, if the query specifies one,
  11. type of the edge should match one in the query, if the query specifies one,
  12. object link target should match one in the query, if the query specifies one,
  13. the number of spans in the edge justification should be no more than two (or NULL for task3 graph response),
  14. the document matches the name of the parent directory for task1 responses,
  15. the query ID taken from the filename matches one in the queries file,
  16. all members of a cluster in the output obtained by applying TA3 graph query against a KB (using NIST's SPARQL query application docker) have the same type.

In addition, if confidence or importance value is specified in scientific notation, the value will be converted to standard notation with a warning.

### Revision history

#### v2019.0.2:
- Code modified to validate the output of recently updated TA3 graph query included in NIST's SPARQL query application docker version 2.5.

#### v2019.0.1:
- Code modifed to validate if all members of a cluster in the output obtained by applying TA3 graph query against a KB (using NIST's SPARQL query application docker) have the same type.
- Hotfix on 6/20/2019: (1) validation of edge type in response fixed, (2) response key changed to filename:linenum

#### v2019.0.0:
- First version of the validator to work on SPARQL output files for M18.

#### v2018.0.3:
- Validator generated false alarm when in a zerohop query response it saw justification span from document elements belonging to multiple parents. (Thank you Hans for reporting the issue).
- Changes an error message for error code “UNEXPECTED_SUBJECT_ENTTYPE” to make it more helpful. (This update was also applied as a hotfix to the v2018.0.2 release branch).

#### v2018.0.2:
- Scope does not need to be specified explicitly therefore switch -scope has been removed; In the new version, scope is internally inferred from the filename of the response file being validated. If the filename is TA2.[class|zerohop|graph]_responses.xml `withincorpus` scope is used and if the filename is DOCID.[class|zerohop|graph]_responses.xml `withindoc` scope is internally used. Please note that `DOCID` is the ID corresponding to the (parent or root) `document` (and that it is not the ID of the `document element` aka `child document`).
- Validator generated false alarm when in a class query response it saw justification span from document elements belonging to multiple parents. (Thank you Hans for reporting the issue).
- Validator has been expanded to check if the justification type (TEXT, IMAGE, VIDEO) matches document element type (bmp, ltf, mp4, etc.).
- Changes an error message for error code “UNEXPECTED_SUBJECT_ENTTYPE” to make it more helpful.

#### v2018.0.1:
- The validator crashed without proper error message when an unexpected edgeid was provided. (Thank you Ryan for reporting the problem).

#### v2018.0.0:
- Original version

### Some notes

- The file specified in place of `docid_mappings` is a tsv file that is originally from LDC but is modified by NIST. This file will be provided along with the query files.
- The above script(s) assume that the output file and error log file do not exist.
- The file specified in place of `queries_dtd` or `responses_dtd` must not have any comments in it. Again, this file will be provided along with the queries file. Six DTD files will be provided, which should not be renamed nor the content be changed without approval:

	1/2. class_[query|response].dtd

	3/4. zerohop_[query|response].dtd

	5/6. graph_[query|response].dtd
