# How to run the AIDA evaluation pipeline

* [Introduction](#introduction)
* [How to build the docker image?](#how-to-build-the-docker-image)
* [How to apply the docker on a test run?](#how-to-apply-the-docker-on-a-test-run)
* [How to apply the docker to your run?](#how-to-apply-the-docker-to-your-run)
* [What should the input directory contain?](#what-should-the-input-directory-contain)
* [What does the output directory contain?](#what-does-the-output-directory-contain)
* [What does the logs directory contain?](#what-does-the-logs-directory-contain)

# Introduction

This document describes how to run the AIDA Task1 evaluation pipeline for M36 practice data using the AIDA-Evaluation docker as a standalone utility.

In order to build the docker image it is important that you have access to the following:

1. GraphDB -- ./docker/AUX-data/M36-practice/graphdb-free-9.3.3-dist.zip

  The AIDA-Evaluation docker uses GraphDB as the triple-store for storing (and applying queries against) the KBs represented in the AIDA Interchange Format. The docker has been tested with `graphdb-free-9.3.3-dist.zip`. The being the free version comes with the limitation of being able to run no more than two queries in parallel. GraphDB can be downloaded from `https://www.ontotext.com/free-graphdb-download/`.

  This document also describes how to use build the docker image using a different version of GraphDB.

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to build the docker image?

1. Place the following files (see [Introduction](#introduction) for details) inside the directory at `./docker/AUX-data/M36-practice`:
  * graphdb-free-9.3.3-dist.zip

2. Make change to the first line (as shown below) of `./docker/Makefile` in order to update the value of variable `ROOT` to reflect your system specific location of directory where the code form the [AIDA evaluation repository](https://github.com/shahraj81/aida) is placed:

  ~~~
  ROOT=/absolute/path/to/aida/tools/aida-evaluation
  ~~~

3. Run the following command:

  ~~~
  cd docker
  make build
  ~~~

  ## Using another version of GraphDB

  In order to build the docker with either a different version of GraphDB you would need to:

  1. Download the paid version of GraphDB `graphdb-[otheredition]-[otherversion]-dist.zip` and place it inside `docker/AUX-data/`, and

  2. Run the following command:

  ~~~
  cd docker
  make build GRAPHDB_EDITION=otheredition GRAPHDB_VERSION=otherversion
  ~~~

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to apply the docker on a test run?

  The docker comes with an example run stored at `./M36-practice/runs/example-run` and the corresponding output stored at `./M36-practice/scores/example-run`.

  Note that the docker expects the output directory to be empty.

  In order to run the docker on the example run, you may execute the following:

  ~~~
  cd docker
  make run
  ~~~

  If you see the message `ERROR: Output directory /score is not empty`, you would need to remove the pre-existing output by running the following command:

  ~~~
  rm -rf ./M36-practice/scores/example-run/*
  ~~~

  You may compare your output with expected output by running the following command:

  ~~~
  git diff
  ~~~

  The only difference that you should see is the timestamps inside file `./M36-practice/scores/example-run/logs/run.log`. All other lines in this file, and content of all other files should remain unchanged.

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to apply the docker to your run?

In order to run the docker on your run, you will need to specify the following when calling `make run`:

  1. The Run ID,
  2. The input directory, and
  3. The output directory.

You may run the following command after changing the values for the variables RUNID, HOST_INPUT_DIR, and HOST_OUTPUT_DIR.

~~~
make run \
      RUNID=your_run_id \
      HOST_INPUT_DIR=/absolute/path/to/your/run \
      HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

[top](#how-to-run-the-aida-evaluation-pipeline)

# What should the input directory contain?
The input directory should contain all the task1 KBs along with corresponding AIF report files. You may want to look at the input directory of the included example run at `./M36-practice/scores/example-run` to get an idea of how to structure your input directory.

[top](#how-to-run-the-aida-evaluation-pipeline)

# What does the output directory contain?

The output directory contains the following:

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

[top](#how-to-run-the-aida-evaluation-pipeline)

# What does the logs directory contain?

The logs directory contains the following log files:

| Name                            |  Description            |
| --------------------------------|-------------------------|
| align-clusters.log              | The log file generated when aligning gold and system clusters. |
| filter-responses.log            | The log file generated when filtering responses. |
| run.log                         | The main log file recording major events by the docker. |
| score_submission.log            | The log file generated by the scorer. |
| validate-responses.log          | The log file generated by the validator. |

[top](#how-to-run-the-aida-evaluation-pipeline)

# Revision History

## 08/31/2020:
* Temporal Metric is being computed.
* Two variant of Argument Metric being computed.
* Entities, Relations, and Events only aggregated being computed.
* Lines in score output files have been sorted before printing.
* Debug information added showing how type metric score was computed.
* Printing system-gold cluster similarities.
* Total number of errors in log files being reported in results.json file.

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
