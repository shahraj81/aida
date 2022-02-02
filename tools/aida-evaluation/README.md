# How to run the AIDA evaluation pipeline

* [Introduction](#introduction)
* [How to build the docker image?](#how-to-build-the-docker-image)
* [How to apply the docker to a test run?](#how-to-apply-the-docker-to-a-test-run)
* [How to apply the docker to your run?](#how-to-apply-the-docker-to-your-run)
* [How to apply the docker to your run in the evaluation setting?](#how-to-apply-the-docker-to-your-run-in-the-evaluation-setting)
* [What should the input directory contain?](#what-should-the-input-directory-contain)
* [What does the output directory contain?](#what-does-the-output-directory-contain)
* [What does the logs directory contain?](#what-does-the-logs-directory-contain)
* [Revision History](#revision-history)

# Introduction

This document describes how to run the AIDA Task1/2/3 evaluation pipeline as part of the AIDA-Evaluation docker as a standalone utility.

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to build the docker image?

The docker has been tested with `graphdb-free-9.10.2-dist` but this section also describes how to configure it to work with a different version.

Independent of which version of GraphDB is being used, first update the value of the variable named `ROOT` at the first line of `./docker/Makefile` to reflect your system specific location of the directory where the code form the [AIDA evaluation repository](https://github.com/shahraj81/aida) is placed. The line to be updated is shown below for completeness:

  ~~~
  ROOT=/absolute/path/to/aida/tools/aida-evaluation
  ~~~

## Using the tested version of GraphDB

In order to build the docker image with the tested version of GraphDB:

1. Download the installer `graphdb-free-9.10.2-dist.zip` from `https://www.ontotext.com/free-graphdb-download/`
2. Place the installer inside `./docker/` and
3. Run the following command:

  ~~~
  cd docker
  make build
  ~~~

## Using another version of GraphDB

In order to build the docker image with a different version of GraphDB:

1. Download the installer of the preferred GraphDB version (the name of which must be of the form`graphdb-[otheredition]-[otherversion]-dist.zip`)
2. place the installer inside `./docker/` and
3. Run the following command:

~~~
cd docker
make build GRAPHDB_EDITION=otheredition GRAPHDB_VERSION=otherversion
~~~

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to apply the docker to a test run?

The docker contains three example practice runs one for each task. The runs are stored at `./M54-practice/runs/` and the corresponding output is stored at `./M54-practice/scores`.

In order to run the docker on the `task1` example run, you may execute the following:

~~~
cd docker
make task1-example
~~~

Note that at this point the task1 docker only runs up to the validation step for Phase 3. The scorer and the other related scripts will be added as soon as possible. 

In order to run the docker on the `task2` example run, you may execute the following:

~~~
cd docker
make task2-example
~~~

In order to run the docker on the `task3` example run, you may execute the following:

~~~
cd docker
make task3-example
~~~

Note that the docker expects the output directory to be empty. If you see the message `ERROR: Output directory /score is not empty`, you would need to remove the pre-existing output.

You may compare your output with the expected output by running the following command:

~~~
git diff
~~~

The only difference that you should see is in the timestamps inside the log files. Content of all other files should remain unchanged.

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to apply the docker to your run?

## How to apply the docker to a task1 run?

In order to run the docker on a `task1` run, use the following command:

~~~
make task1 \
  RUNID=your_run_id \
  HOST_INPUT_DIR=/absolute/path/to/your/run \
  HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

[top](#how-to-run-the-aida-evaluation-pipeline)

## How to apply the docker to a task2 run?

In order to run the docker on a `task2` KB you may run the following command:

~~~
make task2 \
  RUNID=your_run_id \
  HOST_INPUT_DIR=/absolute/path/to/your/run \
  HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

For `task2` the docker expects either the a KB or an S3 location of the KB as input. The name of the file (in the input directory `HOST_INPUT_DIR`) tells the docker whether the input is a KB or an S3 location of the KB (see below for details).

### Providing Task2 KB
When the input is a KB the name of the file should be `task2_kb.ttl`.

### Providing S3 location of Task2 KB
When the input is an S3 location of the KB, the file should be named `s3_location.txt`. The docker expects exactly one line in this file, and that line should be of the form:

~~~
s3://aida-phase2-ta-performers/.../*-nist.tgz
~~~

The compressed file at the above location should expand into a directory containing a sub-directory called `NIST` which should contain a single file (with extension ttl) containing task2 KB.

Note that when supplying an S3 location you must also provide your own AWS credentials using for example the following command:

~~~
make task2 \
  RUNID=your_run_id \
  AWS_ACCESS_KEY_ID=your_aws_access_key_id \
  AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key \
  HOST_INPUT_DIR=/absolute/path/to/your/run \
  HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

[top](#how-to-run-the-aida-evaluation-pipeline)

## How to apply the docker to a task3 run?

Applying the docker to a task3 run is similar to that of task2, except that you would need to call `make task3 ...` instead of `make task2 ...`.

[top](#how-to-run-the-aida-evaluation-pipeline)

# What should the input directory contain?

For `task1`, the input directory should contain all the `task1` KBs along with corresponding AIF report files.

For `task2`, see the section: [How to apply the docker to a task2 run?](#how-to-apply-the-docker-to-a-task2-run) for details on the input directory structure.

For `task3`, the input directory should contain all the `task3` claim KBs along with corresponding report files from the AIF validator, if any.

You may also want to take a look at the input directories of the included example runs located at `./M54-practice/runs/` to get an idea of how to structure your input directories.

[top](#how-to-run-the-aida-evaluation-pipeline)

# What does the output directory contain?

The `task1` output directory contains the following:

| Name                      |  Description                                          |
| --------------------------|-------------------------------------------------------|
| logs                      | The directory containing log files. (See the [section on logs](#what-does-the-logs-directory-contain) for more details). |
| queries                   | The directory containing SPARQL queries applied to KBs. |
| SPARQL-CLEAN-output       | The directory containing cleaned SPARQL output. |
| SPARQL-KB-input           | The directory containing KBs validated by AIF validator. SPARQL queries are applied to these KBs.|
| SPARQL-output             | The directory containing output of SPARQL queries when applied to KBs in `SPARQL-KB-input`. |
| SPARQL-VALID-output       | The directory containing valid SPARQL output. |

## Task2

The `task2` output directory contains the following:

| Name                      |  Description                                          |
| --------------------------|-------------------------------------------------------|
| logs                      | The directory containing log files. (See the [section on logs](#what-does-the-logs-directory-contain) for more details). |
| queries                   | The directory containing SPARQL queries applied to KBs. |
| SPARQL-CLEAN-output       | The directory containing cleaned SPARQL output. |
| SPARQL-KB-source          | The directory containing AWS location of the KB (if available). |
| SPARQL-KB-input           | The directory containing KBs to which SPARQL queries were applied.|
| SPARQL-output             | The directory containing output of SPARQL queries when applied to KBs in `SPARQL-KB-input`. |
| SPARQL-VALID-output       | The directory containing valid SPARQL output. |


## Task3

The `task3` output directory contains the following:

| Name                      |  Description                                          |
| --------------------------|-------------------------------------------------------|
| logs                      | The directory containing log files. (See the [section on logs](#what-does-the-logs-directory-contain) for more details). |
| queries                   | The directory containing SPARQL queries applied to KBs. |
| SPARQL-KB-source          | The directory containing AWS location of the KB (if available). |
| SPARQL-KB-input           | The directory containing KBs to which SPARQL queries were applied.|
| SPARQL-output             | The directory containing output of SPARQL queries when applied to KBs in `SPARQL-KB-input`. |
| SPARQL-CLEAN-output       | The directory containing cleaned SPARQL output. |
| SPARQL-MERGED-output      | The directory containing merged SPARQL output. |
| SPARQL-VALID-output       | The directory containing valid SPARQL output. |

[top](#how-to-run-the-aida-evaluation-pipeline)

# What does the logs directory contain?

The `task1` logs directory contains the following log files:

| Name                            |  Description            |
| --------------------------------|-------------------------|
| run.log                         | The main log file recording major events by the docker. |
| validate-responses.log          | The log file generated by the validator. |

## Task2

The `task2` logs directory contains the following log files:

| Name                            |  Description            |
| --------------------------------|-------------------------|
| run.log                         | The main log file recording major events by the docker. |
| validate-responses.log          | The log file generated by the validator. |


## Task3

The `task3` logs directory contains the following log files:

| Name                            |  Description            |
| --------------------------------|-------------------------|
| run.log                         | The main log file recording major events by the docker. |
| validate-responses.log          | The log file generated by the validator. |
| merge-output.log                | The log file generated by the script that merges output from the two variants of graph queries into one. |
| generate-arf.log                | The log file generated by the ARF generartor. |

[top](#how-to-run-the-aida-evaluation-pipeline)

# Revision History

## 02/02/2022:
* Task1 evaluation pipeline processing up to the validation step added.
* Task2 evaluation pipeline added.
* README revised accordingly.

## 01/26/2022:
* Graphdb version with which the code has been tested updated to the latest version available.

## 01/21/2022:
* Evaluation pipeline modified to use M54-practice data by default instead of the M54-develop data.

## 01/12/2022:
* Evaluation pipeline modified to work on Phase3 Task3 input. This README has been revised accordingly.

## 11/10/2020:
* Evaluation pipeline modified to work on Task3 input. This README has been revised accordingly.

## 10/20/2020:
* Evaluation pipeline modified to work on Task2 input. This README has been revised accordingly.
* The functionality of the task1 side of the pipeline is unchanged except that in order to call the docker for a task1 system you would call `make task1` instead of `make run`.

## 10/05/2020:
* Bugfix: Code crashed if it encountered partially specified date of an aligned event or relation. Validator modified to fill in day/month if day/month was unspecified (No change to the fact that date is considered not present if year is unspecified even if day or month were provided).

## 10/02/2020:
* Bugfix: Code fixed to avoid crashing when it encountered unexpected document element ID.
* Bugfix: typo corrected in code.

## 10/01/2020:
* Code modified to add a parameter `weighted` to the constructor of class `Clusters`. This parameter controls how the similarity between a pair of gold and system event clusters (or relation clusters) is calculated. When `weighted` has the default value "no", the similarity will be the number of aligned pairs of gold-system mentions that have an IOU > selected_threshold (current default=0.1) between spans. However, if `weighted` is set to "yes", the similarity value would be the sum of IOU across all aligned pairs of system-and-gold mentions constraint by the fact that the IOU > selected_threshold (current default=0.1).
* Code changed to support extraction of metatype corresponding to the annotated type.
* Bugfix: typo corrected in code.

## 09/25/2020:
* Implemented relaxed filter for determining which mentions are evaluable. Default strategy for filtering still remains to be the strict one. In order to understand the difference between the strict filter and the relaxed one, let `M` be a mention with span `MS` and type `MT`, `R` be the annotated region with span `RS`, and `RT` be the type exhausitvely annotated in `RS`. `M` would pass the strict filter if and only if `MS` has some non-zero overlap with `RS`, and `MT` be either the same as `RT` or be a finer-grained type of `RT`. However, in order for `M` to pass the relaxed filter, in addition to having a non-zero span overlap between `MS` and `RS`, only the top-level types of `MT` and `RT` should match.

## 09/24/2020:
* Changed IOU thresholds from 0.8 to 0.1.
* Section `How to apply the docker to your run in the evaluation setting?` added to this README to describe how to run the docker using evaluation data (rather than the default practice data). This option is intended for the leaderboard, and not for individual performers.
* Align responses restricted to core documents only.
* Changing scripts to make them work on evaluation data.

## 09/22/2020:
* Allowing IOU thresholds to be specified when running the docker.
* Section `How to apply the docker to your run?` in this README revised to explain how to specify non-default values of IOU thresholds.
* Sanity checks added.

## 09/15/2020:
* The error message, which is generated when a response entry (i.e. line) is removed by filter because none of the system mentions corresponding to one or more clusters in the response entry fall within exhaustively annotated regions, is modified to make the message more clear.

## 09/14/2020:
* A bug has been fixed which at the time of printing similarity values generated zeros for relations. This bug had no impact on scores, however.
* A bug in TRF alignment was discovered in Argument Metric scorers, the correction was made in V1 scorer. V2 scorer was modified to: (1) inherit code from V1 scorer, and (2) override the definition of predicate justification correctness. For V1 scorer, a system TRF is aligned to a gold TRF if both have a matching type and rolename, and both arguments were aligned. For V2 scorer, TRF alignement requires meeting an addition requirement i.e. at least one of the two highest confident system predicate justifications should have some overlap with a gold predicate justification (previously the overlap was required to have an IOU of 0.8 or above).
* Processed parent-children file modified to include language information.
* Breaking up scores by language and metatype.
* Scores in results.json file updated to include scores broken down by language and metatype.

## 09/05/2020:
* A field in results.json file added to report if fatal error was encountered.
* The aida evaluation docker modified to work for open performers with basic error handling if expected files were missing or empty.
* Bugfix: frame-metric scorer updated to remove gold event clusters from output that had no argument.
* Reporting error stats in results.json file.

## 09/04/2020:
* Logger modified to record error code in the log output file for reporting stats.
* Validator modified to correct off-boundary spans if possible otherwise throw them out as invalid.
* Validator modified to generate empty output file (but with header) when all the lines in file being validated are invalid.
* Validator modified to remove all lines from argument-metric and temporal-metric SPARQL output files  if all line corresponding to the subject cluster (or to the object cluster when applicable) in the corresponding corerference-metric SPARQL output file are invalid.
* Response filtering script modified to print header even if the output file is empty.

## 09/03/2020:
* Bug fix: logger can't call get('code_location') therefore get code_location through an object of aida:Object.

## 09/02/2020:
* A minor update: logs files that were generated when scoring example run were updated to reflect no errors in example-run.

## 09/01/2020:
* Release version changed to AIDAED-v2020.1.0
* Score being generated by comparing against gold generated from LDC2020E29_AIDA_Phase_2_Practice_Topic_Annotation_V2.0.
* Order of summary lines in selected score output files changed.
* Bug fixed: An event without arguments in gold is not an error.
* Renaming LDC2020E11.coredocs-29.txt to LDC2020E11.coredocs-xx.txt to smoothly transition from practice into evaluation.
* Mounting data to the docker at run-time to allow changing AUX-data, gold and queries at docker run-time to allow using different directory at the time of evalution (i.e. beyond practice).
* Example run and scores revised.
* Location where graphdb installer is expected is changed to smoothly transition from practice into evaluation.

## 08/31/2020:
* Temporal Metric is being computed.
* Two variant of Argument Metric being computed.
* Entities, Relations, and Events only aggregated being computed.
* Lines in score output files have been sorted before printing.
* Debug information added showing how type metric score was computed.
* Printing system-gold cluster similarities.
* Total number of errors in log files being reported in results.json file.
* Key corresponding to the score for Temporal Metric in results.json file corrected, and renamed from 'TemporalMetric_F1' to 'TemporalMetric_S'.
* A bug in Frame Metric scorer corrected.

## 08/26/2020:
* JPG files were not included in the boundary files due to a typo in the boundary file generator. These have now been included in the docker. Note that while fixing this bug, we discovered that IC001VGHH.jpg had some encoding error due to which the boundary file has a width-height of 0x0 corresponding to this image.
* Using LDC's regions file (in NIST format) rather than the one constructed by NIST using spans from annotations. NIST constructed one was used previously due to a misunderstanding.
* Type Metric scorer has been revised to compute scores using augmented types by restricting finer grain types to only the types that were annotated in the document.

## 08/24/2020:
* Replaced reference KBID LDC2019E44 in example KBs with REFKB.
* Handle the case when cluster ID is 'None' in the alignment table.
* Example run, gold, and queries changed to reflect new prefixes in AIF.
* Removed relations from type metric score.
* Include only events and relations in frame metric score.

## 08/23/2020:
* Handled cases when the system document has no responses.

## 08/22/2020:
* Initial version for M36 practice evaluation.

## 06/15/2020:
* Applying SPARQL queries to only KB that were part of the core-18 documents.
* Increased the java heap space.

## 05/29/2020:
* Initial version.

[top](#how-to-run-the-aida-evaluation-pipeline)
