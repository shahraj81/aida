# How to run the AIDA evaluation pipeline

* [Introduction](#introduction)
* [How to build the docker image?](#how-to-build-the-docker-image)
* [How to apply the docker on a test run?](#how-to-apply-the-docker-on-a-test-run)
* [How to apply the docker to your run?](#how-to-apply-the-docker-to-your-run)
* [How to apply the docker to your run in the evaluation setting?](#how-to-apply-the-docker-to-your-run-in-the-evaluation-setting)
* [What should the input directory contain?](#what-should-the-input-directory-contain)
* [What does the output directory contain?](#what-does-the-output-directory-contain)
* [What does the logs directory contain?](#what-does-the-logs-directory-contain)
* [Revision History](#revision-history)

# Introduction

This document describes how to run the AIDA Task1/Task2 evaluation pipeline for M36 practice data using the AIDA-Evaluation docker as a standalone utility.

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to build the docker image?

The docker has been tested with `graphdb-free-9.3.3-dist` but this section also describes how to configure it to work with a different version.

Independent of which version of GraphDB you are using, you would need to first update the value of the variable named `ROOT` at the first line of `./docker/Makefile` (as shown below) to reflect your system specific location of the directory where the code form the [AIDA evaluation repository](https://github.com/shahraj81/aida) is placed:

  ~~~
  ROOT=/absolute/path/to/aida/tools/aida-evaluation
  ~~~

## Using the tested version of GraphDB

In order to build the docker image with the tested version of GraphDB you would need to:

1. Download `graphdb-free-9.3.3-dist.zip` from `https://www.ontotext.com/free-graphdb-download/`, and place it inside `./docker/`, and

2. Run the following command:

  ~~~
  cd docker
  make build
  ~~~

## Using another version of GraphDB

In order to build the docker image with a different version of GraphDB you would need to:

1. Download the installer of the GraphDB version that you would like to use (the name of which must be of the form`graphdb-[otheredition]-[otherversion]-dist.zip`), and place it inside `./docker/`, and

2. Run the following command:

~~~
cd docker
make build GRAPHDB_EDITION=otheredition GRAPHDB_VERSION=otherversion
~~~

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to apply the docker on a test run?

The docker comes loaded with two example runs: one for `task1` and the other for `task2`. The example runs are stored at `./M36-practice/runs/example-task1-run` and `./M36-practice/runs/example-task2-run`, respectively, and the output is stored at `./M36-practice/scores/example-task1-run` and `./M36-practice/scores/example-task2-run`, respectively.

Note that the docker expects the output directory to be empty.

In order to run the docker on the `task1` example run, you may execute the following:

~~~
cd docker
make task1-example
~~~

In order to run the docker on the `task2` example run, you may execute the following:

~~~
cd docker
make task2-example
~~~

If you see the message `ERROR: Output directory /score is not empty`, you would need to remove the pre-existing output.

You may compare your output with the expected output by running the following command:

~~~
git diff
~~~

The only difference that you should see is in the timestamps inside the log files. Content of all other files should remain unchanged.

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to apply the docker to your run?

## How to apply the docker to a task1 run?

In order to run the docker on a `task1` run, you will need to specify the following when calling `make task1`:

  1. The Run ID,
  2. The input directory, and
  3. The output directory.

You may run the following command after changing the values for the variables RUNID, HOST_INPUT_DIR, and HOST_OUTPUT_DIR.

~~~
make task1 \
  RUNID=your_run_id \
  HOST_INPUT_DIR=/absolute/path/to/your/run \
  HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

Note that the scorer uses a default value of 0.1 for all IOU thresholds. If you would like to change these values, you may update thresholds on the following line of the Makefile:

~~~
ENG_TEXT_IOU_THRESHOLD=0.1
SPA_TEXT_IOU_THRESHOLD=0.1
RUS_TEXT_IOU_THRESHOLD=0.1
IMAGE_IOU_THRESHOLD=0.1
VIDEO_IOU_THRESHOLD=0.1
~~~

Alternatively, you may also supply the new values when you run the docker using:

~~~
make task1 \
  RUNID=your_run_id \
  ENG_TEXT_IOU_THRESHOLD=your_threshold \
  SPA_TEXT_IOU_THRESHOLD=your_threshold \
  RUS_TEXT_IOU_THRESHOLD=your_threshold \
  IMAGE_IOU_THRESHOLD=your_threshold \
  VIDEO_IOU_THRESHOLD=your_threshold \
  HOST_INPUT_DIR=/absolute/path/to/your/run \
  HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

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

# How to apply the docker to your run in the evaluation setting?

This section is written for the leaderboard usage or NIST-internal usage.

In order to run the docker on the `evaluation` data (rather than the default `practice` data), you would need to supply the value `evaluation` to the variable named `RUNTYPE` when calling `make task1` or `make task2` by modifying the Makefile to reflect the following:

~~~
RUNTYPE=evaluation
~~~

Alternatively, you may run the following command for `task1`:

~~~
make task1 \
  RUNID=your_run_id \
  RUNTYPE=evaluation
  ENG_TEXT_IOU_THRESHOLD=your_threshold \
  SPA_TEXT_IOU_THRESHOLD=your_threshold \
  RUS_TEXT_IOU_THRESHOLD=your_threshold \
  IMAGE_IOU_THRESHOLD=your_threshold \
  VIDEO_IOU_THRESHOLD=your_threshold \
  HOST_DATA_DIR=/absolute/path/to/auxiliary_evaluation_data \
  HOST_INPUT_DIR=/absolute/path/to/your/run \
  HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

In order to run the docker in the evaluation setting for `task2` you may run the following command when providing the KB as input:

~~~
make task2 \
  RUNID=your_run_id \
  RUNTYPE=evaluation \
  HOST_DATA_DIR=/absolute/path/to/auxiliary_evaluation_data \
  HOST_INPUT_DIR=/absolute/path/to/your/run \
  HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

You may run the following command when providing the S3 location of the `task2` KB as input:

~~~
make task2 \
  RUNID=your_run_id \
  RUNTYPE=evaluation \
  AWS_ACCESS_KEY_ID=your_aws_access_key_id \
  AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key \
  HOST_DATA_DIR=/absolute/path/to/auxiliary_evaluation_data \
  HOST_INPUT_DIR=/absolute/path/to/your/run \
  HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

Note that you must specify the required `evaluation` auxiliary data, driven from the evaluation corpus and annotations, by changing the default value of the variable `HOST_DATA_DIR`. The default value of this variable points to the `practice` auxiliary data, driven from the practice corpus and annotations, and using this default value will make the docker run in the `practice` setting.

[top](#how-to-run-the-aida-evaluation-pipeline)

# What should the input directory contain?
For `task1`, the input directory should contain all the `task1` KBs along with corresponding AIF report files.

See the section: [How to apply the docker to a task2 run?](#how-to-apply-the-docker-to-a-task2-run) for details on the input directory structure for `task2` submission.

You may also want to take a look at the input directories of the `task1` and `task2` example runs located at `./M36-practice/runs/` to get an idea of how to structure your input directories.

[top](#how-to-run-the-aida-evaluation-pipeline)

# What does the output directory contain?

## Task1

The `task1` output directory contains the following:

| Name                      |  Description                                          |
| --------------------------|-------------------------------------------------------|
| alignment                 | The directory containing information about alignment between system and gold clusters. |
| logs                      | The directory containing log files. (See the [section on logs](#what-does-the-logs-directory-contain) for more details). |
| queries                   | The directory containing SPARQL queries applied to KBs. |
| results.json              | The results JSON file to be used by the leaderboard. |
| scores                    | The directory containing various task1 scores. |
| similarities              | The directory containing information about similarities between system clusters, and between gold clusters. |
| SPARQL-CLEAN-output       | The directory containing cleaned SPARQL output. |
| SPARQL-FILTERED-output    | The directory containing filtered responses i.e. responses that are within annotated regions. |
| SPARQL-KB-input           | The directory containing KBs validated by AIF validator. SPARQL queries are applied to these KBs.|
| SPARQL-output             | The directory containing output of SPARQL queries when applied to KBs in `SPARQL-KB-input`. |
| SPARQL-VALID-output       | The directory containing valid SPARQL output. |

## Task2

The `task2` output directory contains the following:

| Name                      |  Description                                          |
| --------------------------|-------------------------------------------------------|
| logs                      | The directory containing log files. (See the [section on logs](#what-does-the-logs-directory-contain) for more details). |
| queries                   | The directory containing SPARQL queries applied to KBs. |
| SPARQL-KB-input           | The directory containing KBs to which SPARQL queries were applied.|
| SPARQL-output             | The directory containing output of SPARQL queries when applied to KBs in `SPARQL-KB-input`. |
| SPARQL-VALID-output       | The directory containing valid SPARQL output. |

[top](#how-to-run-the-aida-evaluation-pipeline)

# What does the logs directory contain?

## Task1

The `task1` logs directory contains the following log files:

| Name                            |  Description            |
| --------------------------------|-------------------------|
| align-clusters.log              | The log file generated when aligning gold and system clusters. |
| filter-responses.log            | The log file generated when filtering responses. |
| run.log                         | The main log file recording major events by the docker. |
| score_submission.log            | The log file generated by the scorer. |
| validate-responses.log          | The log file generated by the validator. |

## Task2

The `task2` logs directory contains the following log files:

| Name                            |  Description            |
| --------------------------------|-------------------------|
| run.log                         | The main log file recording major events by the docker. |
| validate-responses.log          | The log file generated by the validator. |

[top](#how-to-run-the-aida-evaluation-pipeline)

# Revision History

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
