# How to run the AIDA evaluation pipeline

* [Introduction](#introduction)
* [How to build the docker image?](#how-to-build-the-docker-image)
* [How to apply the docker on a test run?](#how-to-apply-the-docker-on-a-test-run)
* [How to apply the docker on your run?](#how-to-apply-the-docker-on-your-run)
* [What should be in the input directory?](#what-should-be-in-the-input-directory)
* [What is contained in the output directory?](#what-is-contained-in-the-output-directory)
* [What is contained in the logs directory?](#what-is-contained-in-the-logs-directory)

# Introduction

This document describes how to run the AIDA evaluation pipeline for M18 re-run using the AIDA-Evaluation docker as a standalone utility to task1 KBs.

In order to build the docker image it is important that you have access to the following:

1. GraphDB -- ./docker/AUX-data/M18/graphdb-free-9.2.1-dist.zip

  The AIDA-Evaluation docker uses GraphDB as the triple-store for storing (and applying queries against) the KBs represented in the AIDA Interchange Format. The docker has been tested with `graphdb-free-9.2.1-dist.zip`. NOTE that the free version comes with the limitation of being able to run no more than two queries in parallel.

  In order to make use of one of GraphDBs paid version (or another free version) place the installer in AUX-data/M18 and supply the corresponding values for variables `GRAPHDB_VERSION` and `GRAPHDB_EDITION` to make when invoking `make build`.

  In order to build the docker with the free version, make sure to download the installer from `https://www.ontotext.com/free-graphdb-download/` and place it at: `./docker/AUX-data/M18/graphdb-free-9.2.1-dist.zip`

2. The M18 Evaluation Queries -- ./docker/AUX-data/M18/AIDA_Phase1_Evaluation_Queries_V8.tgz

  The AIDA M18 evaluation queries can be downloaded from [AIDA Phase1 Evaluation Queries V8](https://tac.nist.gov/protected/2019-kbp/data/AIDA_Phase1_Evaluation_Queries_V8.tgz).

3. Assessments Package -- ./AUX-data/M18/LDC2019R30_AIDA_Phase_1_Assessment_Results_V6.1.tgz

  The assessment package as received from LDC. Place the assessments package at './AUX-data/M18/LDC2019R30_AIDA_Phase_1_Assessment_Results_V6.1.tgz' before building the docker.

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to build the docker image?

1. Place the following files (see [Introduction](#introduction) for details) in './docker/AUX-data/M18':
  * graphdb-free-9.2.1-dist.zip
  * AIDA_Phase1_Evaluation_Queries_V8.tgz
  * LDC2019R30_AIDA_Phase_1_Assessment_Results_V6.1.tgz

2. Make change to the first line (as shown below) of './docker/Makefile' in order to update the value of variable ROOT to reflect your system directory where the code form the [AIDA evaluation repository](https://github.com/shahraj81/aida) is placed:

  ~~~
  ROOT=/absolute/path/to/aida/tools/aida-evaluation
  ~~~

3. Run the following command:

  ~~~
  cd docker
  make build
  ~~~

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to apply the docker on a test run?

  The docker comes with an example run stored at `./M18-data/runs/task1-team-alpha-run-5` and the corresponding output stored at `./M18-data/scores/task1-team-alpha-run-5`.

  Note that the docker expects the output directory to be empty.

  In order to run the docker on the example run, you may execute the following:

  ~~~
  cd docker
  make run
  ~~~

  If you see the message `ERROR: Output directory /score is not empty`, you would need to remove the pre-existing output by running the following command:

  ~~~
  rm -rf ./M18-data/scores/task1-team-alpha-run-5/*
  ~~~

  You may compare your output with expected output by running the following command:

  ~~~
  git diff
  ~~~

  The only difference that you should see is the timestamps inside file `./M18-data/scores/task1-team-alpha-run-5/logs/run.log`. All other lines in this file, and content of all other files should remain unchanged.

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

# What should be in the input directory?
The input directory should contain all the task1 KBs along with corresponding AIF report files. You may want to look at the input directory of the included example run at `/M18-data/runs/task1-team-alpha-run-5` to get an idea of how to structure your input directory.

[top](#how-to-run-the-aida-evaluation-pipeline)

# What is contained in the output directory?

The output directory contains the following:

| Name                |  Description                                          |
| --------------------|-------------------------------------------------------|
| SPARQL-KB-input     | The directory containing KBs validated by AIF validator. SPARQL queries are applied to these KBs.|
| SPARQL-output       | The directory containing output of SPARQL queries when applied to KBs in SPARQL-KB-input. |
| SPARQL-VALID-output | The directory containing valid SPARQL output. This directory will be used as input to the confidence aggregator |
| SPARQL-CA-output    | The directory containing output of the confidence aggregator |
| queries             | The directory containing SPARQL queries applied to KBs. |
| logs                | The directory containing log files. (See the [section on logs](#what-is-contained-in-the-logs-directory) for more details).
| scores              | The directory containing task1 class and graph scores in two separate files: `class-score.txt` and `graph-score.txt` |

[top](#how-to-run-the-aida-evaluation-pipeline)

# What is contained in the logs directory?

The logs directory contains the following log files:

| Name                            |  Description            |
| --------------------------------|-------------------------|
| run.log                         | The main log file recording major events by the docker |
| validate-class-responses.log    | The log file generated by the response validator when validating task1 class responses |
| validate-graph-responses.log    | The log file generated by the response validator when validating task1 graph responses |
| aggregate-class-confidences.log | The log file generated by the confidence aggregator when run on valid task1 class SPARQL output |
| aggregate-graph-confidences.log | The log file generated by the confidence aggregator when run on valid task1 graph SPARQL output |
| class-score.log                 | The log file generated by task1 class scorer |
| graph-score.log                 | The log file generated by task1 graph scorer |

[top](#how-to-run-the-aida-evaluation-pipeline)

# Revision History

## 05/29/2020:
* Initial version.

[top](#how-to-run-the-aida-evaluation-pipeline)
