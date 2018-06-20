# AIDA

Tools and utilities for supporting AIDA evaluations.
Shahzad Rajput.

| Name | Description |
|---|---|
| utils/translate-annotations/seedling | Utility to translate LDC's seedling annotation to turtle-RDF format |

## Translate LDC's seedling annotations to turtle-RDF format

The scripts, data and output for the translation of seedling LDC annotations is at: 

utils/translate-annotations/seedling

### Scripts provided

####(1) AIDA-Translate-MASTER.pl

The main script required for converting LDC's annotations into turtle-RDF format.

####(2) TranslateManagerLib.pm

The library containing all custom packages.

### Data files provided

The following mappings are eventually going to be transparent to the TA1 and TA2 participants and that the data they receive should only have types in NIST defined format, i.e., more descriptive and spelled out rather than short form as they currently appear in LDC's annotation. At this point, we envision that LDC's annotations should be run through a translation by NextCentury to generate RDF and that translated RDF be only made available to  TA1 and TA2 participant in order to avoid confusion, 

####(1) nist-role-mapping-compact-20180618.txt

This file contains role mapping used to translate: 

(a) types (and subtypes) of entities, events and relations, and

(b) role names of event slots and relation slots. 

####(2) nist-type-mapping-20180618.txt

This file contains mapping of LDC-defined types and NIST-defined types. 

### Additional data required for running the script

Place the following LDC packages in the tils/translate-annotations/seedling/data directory:

(a) LDC2018E01_AIDA_Seedling_Corpus_V1

(b) LDC2018E45_AIDA_Scenario_1_Seedling_Annotation_V3.0

### Execution and output

