# Introduction

(Last modified: May 23, 2019)

This document describes:

  1. Usage of confidence aggregation script: `AIDA-ConfidenceAggregation-MASTER.pl`
  2. Input directory specifications
  3. The script in docker form
  4. Revision history

# Usage

~~~
AIDA-ConfidenceAggregation-MASTER.pl:  Aggregate Confidences.

Usage: AIDA-ConfidenceAggregation-MASTER.pl {-switch {-switch ...}} type input output

Legal switches are:
  -error_file <value>  Specify a file to which error output should be redirected
                         (Default = STDERR).
  -help                Show help
  -version             Print version number and exit
parameters are:
  type    Type of the input file (see below for options) (Required).
  input   Input directory containing one of more directories containing SPARQL
            query response files (Required).
  output  Specify an output directory. (Required).

type is one of the following:
  TA1_CL: Input directory contains responses to task1 class queries
  TA1_GR: Input directory contains responses to task1 graph queries
  TA2_GR: Input directory contains responses to task2 graph queries
  TA2_ZH: Input directory contains responses to task2 zerohop queries
~~~

# Input/output directory specifications

The confidence aggregation script runs on the output of NIST SPARQL query application docker for M18. The script assumes the input directory to be containing output of exactly one run. This run could be either a task1 run or a  task2 run.

We expect that the output directory would be empty.

## Task 1

The input directory contains the output of NIST SPARQL query application docker when run over a TA1 system containing KBs corresponding to a set of evaluation documents conditioned upon either no hypothesis (Task 1a) or a single hypothesis (for Task 1b). This directory would contain multiple subdirectories. Each subdirectory corresponds to one task1 KB corresponding to one (parent) document. Within each subdirectory, there will be files matching the following pattern:

~~~
AIDA_TA1_[CL|GR]_2019_\d\d\d\d.rq.tsv
~~~

## Task 2

A task2 run output would contain a single subdirectory. This subdirectory corresponds to a task2 KB. Within each subdirectory, there will be files matching the following pattern:

~~~
AIDA_TA2_[GR|ZH]_2019_\d\d\d\d.rq.tsv
~~~

# The script in docker form

This script has been made into four separate dockers which can be found inside `./dockers` directory:

|   | Docker  | Description |
|---|---------|-------------|
| 1.  | TA1_CL_ConfidenceAggregation | Confidence aggregation docker for task1 class responses |
| 2.  | TA1_GR_ConfidenceAggregation | Confidence aggregation docker for task1 graph responses |
| 3.  | TA2_GR_ConfidenceAggregation | Confidence aggregation docker for task2 graph responses |
| 4.  | TA2_ZH_ConfidenceAggregation | Confidence aggregation docker for task2 zerohop responses |

Please refer to `./dockers/TA[12]_[CL|GR|ZH]_ConfidenceAggregation/README.md` for details.

# Revision history
  * AIDACA-v2019.0.0: First version
  * AIDACA-v2019.0.1: Bugfix: ?edge_cv changed to ?edge_cj_cv
