# How to run the AIDA evaluation pipeline

* [Introduction](#introduction)
* [How to build the docker image?](#how-to-build-the-docker-image)
* [Steps in the dockerized pipeline](#steps-in-the-dockerized-pipeline)
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

The docker has been tested with `graphdb-10.0.2-dist.zip` but this section also describes how to configure it to work with a different version.

Independent of which version of GraphDB is being used, first update the value of the variable named `ROOT` at the first line of `./docker/Makefile` to reflect your system specific location of the directory where the code form the [AIDA evaluation repository](https://github.com/shahraj81/aida) is placed. The line to be updated is shown below for completeness:

  ~~~
  ROOT=/absolute/path/to/aida/tools/aida-evaluation
  ~~~

## Using the tested version of GraphDB

In order to build the docker image with the tested version of GraphDB:

1. Download the installer `graphdb-10.0.2-dist.zip` from `https://www.ontotext.com/free-graphdb-download/`
2. Place the installer inside `./docker/` and
3. Run the following command:

  ~~~
  cd docker
  make build
  ~~~

## Using another free version of GraphDB

In order to build the docker image with a different free version of GraphDB:

1. Download the installer of the preferred GraphDB version (the name of which must be of the form`graphdb-[otherversion]-dist.zip`)
2. place the installer inside `./docker/` and
3. Run the following command:

~~~
cd docker
make build GRAPHDB_VERSION=otherversion
~~~

[top](#how-to-run-the-aida-evaluation-pipeline)

# Steps in the dockerized pipeline

Depending on the task, the dockerized pipeline runs a subset of the following steps in the order given below:

## SPARQL-output (Task1/2/3)

In this step SPARQL queries are applied to the KBs.

## SPARQL-CLEAN-output (Task1/2/3)

SPARQL output contains AIF prefixes attached to values, an example of which is shown below:

~~~
<https://raw.githubusercontent.com/NextCenturyCorporation/AIDA-Interchange-Format/master/java/src/main/resources/com/ncc/aif/ontologies/InterchangeOntology#Relation>
~~~

These prefixes are removed during this cleaning step which reduces the above example to just `Relation`.

## SPARQL-MERGED-output (Task3)

In this step, cleaned SPARQL output from multiple variants of the a SPARQL query (e.g. `AIDA_P3_TA3_GR_0001A.rq` and `AIDA_P3_TA3_GR_0001B.rq`) are merged into a single output file `AIDA_P3_TA3_GR_0001.rq.tsv` in order to process next steps.

## SPARQL-VALID-output (Task1/2/3)

In this step, responses from output of the previous step is validated.

## SPARQL-FILTERED-output (Task1)

In this step, responses from the output of the previous step are used to align clusters and mentions to gold data, and generate filtered SPARQL output.

## Scoring (Task1)

In this step, responses from the output of the previous step are used to generate scores.

## ARF-output (Task3)

In this step task3 validated output is converted to output in assessor readable format (ARF).

[top](#how-to-run-the-aida-evaluation-pipeline)

# How to apply the docker to a test run?

The docker contains example practice runs for each task. The runs are stored at `./M54-practice/runs/` and the corresponding output is stored at `./M54-practice/scores`.

In order to run the docker on the `task1` example run, you may execute the following:

~~~
cd docker
make task1-example
~~~

In order to run the docker with a local (or different version of) KGTK-Similarity service API, set the variable `KGTK_API` to the location of the desired to be used when calling `make` as shown below:

~~~
make task1-example KGTK_API=https://...
~~~

Similarly, if the preference is to not use the API, set the variable `KGTK_API` to None explicitly, as shown below:

~~~
make task1-example KGTK_API=None
~~~

In this case, the docker will compute similarity between qnodes based on identity, and synonyms and near-neighbor information provided in the DWD overlay.

In order to run the docker on the `task2` example run, you may execute the following:

~~~
cd docker
make task2-example
~~~

Three example runs (and corresponding output) for `task3` have been made available. In order to run the docker on these example runs, you may execute the following:

1. `M54-practice/runs/example-task3-run`,
~~~
cd docker
make task3-example
~~~
2. `M54-practice/runs/example-task3-run-aws-1`,
~~~
cd docker
make task3-example-aws-1
~~~
3. `M54-practice/runs/example-task3-run-aws-2`,
~~~
cd docker
make task3-example-aws-2
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

The AIDA evaluation docker can accept a task3 run either via the direct mount or from an S3 location. The format of the input expected by the docker differs depending on how the input is provided, as described below.

### Direct mount

In order to apply the docker to a task3 run that is mounted directly to the docker, run the following command:

~~~
make task3 \
  RUNID=your_run_id \
  HOST_INPUT_DIR=/absolute/path/to/your/run \
  HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

Note that, in this case, the directory structure should be of the form:

~~~
  - your_run_id
  - your_run_id/Condition5
  - your_run_id/Condition5/query_claim_id_1/some_claim_id_11.ttl
  - your_run_id/Condition5/query_claim_id_1/some_claim_id_12.ttl
  - your_run_id/Condition5/query_claim_id_1/some_claim_id_12-report.txt
  - your_run_id/Condition5/query_claim_id_1/...
  - your_run_id/Condition5/query_claim_id_1/query_claim_id_1.ranking.tsv
  - your_run_id/Condition5/query_claim_id_...
  - your_run_id/Condition6/query_topic_1/some_claim_id_21.ttl
  - your_run_id/Condition6/query_topic_1/some_claim_id_22.ttl
  - your_run_id/Condition6/query_topic_1/...
  - your_run_id/Condition6/query_topic_1/query_topic_1.ranking.tsv
  - your_run_id/Condition6/query_topic_...
  - your_run_id/Condition7/query_topic_2/some_claim_id_31.ttl
  - your_run_id/Condition7/query_topic_2/some_claim_id_32.ttl
  - your_run_id/Condition7/query_topic_2/...
  - your_run_id/Condition7/query_topic_2/query_topic_3.ranking.tsv
  - your_run_id/Condition7/query_topic_...
~~~

Note that in the above example `your_run_id/Condition5/query_claim_id_1/some_claim_id_12.ttl` does not have valid AIF due to the presence of the report file `your_run_id/Condition5/query_claim_id_1/some_claim_id_12-report.txt` which is why that claim KB would not be processed.

Also note that a condition directory should not be present if the run does not have a claim KB corresponding to it.

### S3 location

When the input is an S3 location of the run, place a file named `s3_location.txt` inside the input directory. The input directory should not contain any other file or directory in it. The docker expects exactly one line in the `s3_location.txt` file, and that line should be of the form:

~~~
s3://aida-phase2-ta-performers/.../*-nist.tgz
~~~

The compressed file at the above location should expand into a directory of the form:

~~~
  - output/your_run_id/NIST
  - output/your_run_id/NIST/Condition5
  - output/your_run_id/NIST/Condition5/query_claim_id_1/some_claim_id_11.ttl
  - output/your_run_id/NIST/Condition5/query_claim_id_1/some_claim_id_12.ttl
  - output/your_run_id/NIST/Condition5/query_claim_id_1/...
  - output/your_run_id/NIST/Condition5/query_claim_id_1/query_claim_id_1.ranking.tsv
  - output/your_run_id/NIST/Condition5/query_claim_id_...
  - output/your_run_id/NIST/Condition6/query_topic_1/some_claim_id_21.ttl
  - output/your_run_id/NIST/Condition6/query_topic_1/some_claim_id_22.ttl
  - output/your_run_id/NIST/Condition6/query_topic_1/...
  - output/your_run_id/NIST/Condition6/query_topic_1/query_topic_1.ranking.tsv
  - output/your_run_id/NIST/Condition6/query_topic_...
  - output/your_run_id/NIST/Condition7/query_topic_2/some_claim_id_31.ttl
  - output/your_run_id/NIST/Condition7/query_topic_2/some_claim_id_32.ttl
  - output/your_run_id/NIST/Condition7/query_topic_2/...
  - output/your_run_id/NIST/Condition7/query_topic_2/query_topic_3.ranking.tsv
  - output/your_run_id/NIST/Condition7/query_topic_...
~~~

In order to apply the docker to a task3 run that is to be read from an S3 location, run the following command:

~~~
make task3 \
  RUNID=your_run_id \
  AWS_ACCESS_KEY_ID=your_aws_access_key_id \
  AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key \
  HOST_INPUT_DIR=/absolute/path/to/your/run \
  HOST_OUTPUT_DIR=/absolute/path/to/output
~~~

### Using DEPTH to process top-ranked claims

You may optionally use DEPTH to specify the number of top-ranked claims that you would like to be selected for processing through the NIST evaluation pipeline. This option will in particular be helpful for debugging. For example, if you want to process the top-5 claims for each condition, for each user-query, and for each claim-relation (see Section 6.4 of Evaluation Plan v1.1), using the following command:

~~~
make task3 \
  ...
  DEPTH=Condition5:5,Condition6:5,Condition7:5
  ...
~~~

Note that the value of DEPTH should be of the form: `^Condition5:\d+,Condition6:\d+,Condition7:\d$`.

Also note that a condition directory should not be present if the run does not have a claim KB corresponding to it.

### LTF data

Since the source corpus is protected by copyrights, providing LTF data to the docker is optional. If one desires to have missing object handles (objectc_handle), in `AIDA_P3_TA3_GR_*.rq.tsv` files, automatically replaced by text taken from the source corpus using object informative justification span (oinf_j_span) given that oinf_j_span is drawn from a text document, all the ltf files (`*.ltf.xml`), contained in the source corpus, should be placed in a directory named `ltf` inside the auxiliary data directory. Note that the auxiliary data directory is the one that is pointed to by variable named HOST_DATA_DIR in the `./docker/Makefile`.

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

For `task2`, see the section: [How to apply the docker to a task2 run?](#how-to-apply-the-docker-to-a-task2-run) for details on the input directory structure.

For `task3`, the input directory should contain all the `task3` claim KBs along with corresponding report files from the AIF validator, if any. The directory should be structured as mentioned in the Section: [How to apply the docker to your run?](#how-to-apply-the-docker-to-your-run).

You may also want to take a look at the input directories of the included example runs located at `./M54-practice/runs/` to get an idea of how to structure your input directories.

[top](#how-to-run-the-aida-evaluation-pipeline)

# What does the output directory contain?

## Task1

The `task1` output directory contains the following:

| Name                      |  Description                                          |
| --------------------------|-------------------------------------------------------|
| alignment                 | The directory containing information about mention and cluster alignment between system and gold. |
| logs                      | The directory containing log files. (See the [section on logs](#what-does-the-logs-directory-contain) for more details). |
| queries                   | The directory containing SPARQL queries applied to KBs. |
| similarities              | The directory containing similarities between clusters. |
| scores                    | The directory containing scores. |
| SPARQL-CLEAN-output       | The directory containing cleaned SPARQL output. |
| SPARQL-KB-input           | The directory containing KBs validated by AIF validator. SPARQL queries are applied to these KBs.|
| SPARQL-output             | The directory containing output of SPARQL queries when applied to KBs in `SPARQL-KB-input`. |
| SPARQL-VALID-output       | The directory containing valid SPARQL output. |
| SPARQL-FILTERED-output

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

## Task1

The `task1` logs directory contains the following log files:

| Name                            |  Description            |
| --------------------------------|-------------------------|
| filter-responses.log            | The log file generated as part of SPARQL-FILTERED-output. |
| run.log                         | The main log file recording major events by the docker. |
| score-responses.log             | The log file generated as part of scoring. |
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

# Notes

## Caching Task1 Qnode-Qnode similarity scores
When the docker calls the filtering script, the cached similarity scores from the cache-file are loaded into memory, if the file is provided by the docker.

When computing similarity scores between two Q-nodes:
* first the Q-nodes are checked if they are identical, if so the similarity score of 1.0 is returned to the caller,
* if not, the Q-nodes are checked for being synonyms to each other (as per version 5.1a of the DWD overlay), if so the similarity score of 1.0 is returned to the caller,
* If not, the similarity score is looked up in the cache, and returned to the caller,
* if not, the Q-nodes are checked for being near-neighbors of each other (as per version 5.1a of the DWD overlay), simultaneously, the KGTK-similarity score is determined using the KGTK-similarity service API specified when calling the docker. If the nodes were, near-neighbors, similarity score is set to the args.near_neighbor_similarity_value sent as parameter to the filtering script by the docker. If the similarity score computed off of the KGTK-similarity service exceeds the similarity scores, the similariy score is set to the one computed from the KGTK-similarity service. This value is stored in the cache, and returned to the called.

Right after the filtering script is done querying kgtk-similarity service for similarity scores between all pairs of Q-nodes needed for filtering, the cache in memory is flushed to the file. A lock file (args.lock) is used to synchronize calls to flush the cache between multiple threads (if any). The avilability of lock is checked as frentrly as 10 seconds by default but this time can be changed if needed when calling the docker.

## Thresholds

### IOU threshold

IOU threshold of 0.9 is used by default When computing the proportion of spans overlap (IOU), the IOU is set to zero if the IOU does not meet or exceed the IOU-threshold set to 0.9 by default. This threshold can be changed when calling the docker by setting the variable IOU_THRESHOLD to the desired value when calling `make`.

### ALPHA

When checking if a cluster type is similar enough to a taggable DWD ontology type, the similarity between the two types is compared against args.alpha. The types are considered to be similar enough if the similarity exceeds alpha. The value of ALPHA is set to 0.9 by default but can be changed to the desired value when calling `make`.

## Near-neighbor similarity value

When two Q-nodes are found to be near-neighbors, similarity between the two is set to 0.9 by default, but this value can be changed by setting the variable `NN_SIMILARITY_VALUE` to the desired value when calling `make`.

# Revision History

## 10/07/2022:
* controlling ALPHA, CACHE, IOU thresholds, KGTK_API (location), LOCK (file), NN_SIMILARITY_VALUE, SIMILARIY_TYPES, and WAIT (seconds) from docker Makefile
* IOU_THRESHOLDS split by language and modality to give finer control
* using lock to synchronize writing cache updates in multiple instances to file
* using near-neighbors information from dwd overlay
* if needed, pick the highest of the near-neighbor score and the kgtk-similarity based score,
* progress bar added to various steps

## 10/05/2022:
* Option added to specify location of the kgtk-similarity service when calling the docker allowing one to use local installations of the service for speedup in performance; by default https://kgtk.isi.edu/similarity_api is being used
* Option added to specify similarity types used by kgtk-similarity service when calling filter_responses.py
* Caching qnode-qnode similarity values to improve performance; a set of qnode-qnode cached similarity values comes with the docker by default
* Handling ConnectionError, if encountered
* Using batch querying when calling the kgtk similarity service API
* bugfix: get('is_synonym', q1, q2) -> is_synonym(q1, q2)

## 09/28/2022:
* Docker modified to make it work with the latest version of free graphdb v10.0.2.

## 09/26/2022:
* Initial version of task1 scorer for Phase 3.

## 03/31/2022:
* Replacing objectc_handle with text from source corpus if:
  * objectc_handle is missing, and
  * oinf_j_span is drawn from a text document, and
  * ltf_directory is made avaialble to the docker.

## 03/28/2022:
* Removing task3 edges from SPARQL-VALID-output if the source document does not match that of the claim

## 03/25/2022:
* `ec_id` and `ec_similarity` assessment lines added to the outer-claim files in the ARF-output

## 03/10/2022:
* Adding an optional switch --depth to the task3 run script. This switch can take values in the form '^Condition5:\d+,Condition6:\d+,Condition7:\d$'. If provided, for each condition, for each user-query, and for each claim-relation (see Section 6.4 of Evaluation Plan v1.1), top-ranked claims will be selected (as specified using the switch --depth) for processing through the NIST evaluation pipeline.

## 03/09/2022:
* Updating the default GraphDB version to 9.10.3 that came with critical bug fixes

## 03/08/2022:
* When generating ARF, allow missing date for an event or relation

## 03/07/2022:
* A bug was fixed that was causing the ARF generator to crash
* Task3 validator expanded to:
  * clarify error message(s)
  * match topic, subtopic and claimTemplate against those in user-queries
  * mark an AIF-valid claim as invalid if any of the required fields are invalid, and subsequently remove the entire claim from the output generated by NIST response validator

## 02/09/2022:
* Dates mapped to N/A updated in generated ARF
  * '01-01-0001', '31-12-9999', '0001-01-01', '9999-12-31' are mapped to N/A
* Do not generate termporal edges in generated ARF if all the dates were left unspecified (i.e. one from {'01-01-0001', '31-12-9999', '0001-01-01', '9999-12-31'})
* Task3 runs directory structure updated to match one specified in the evaluation plan
* Task3 run can now be read from an S3 location. The directory structure for a task3 run read from an S3 location is different from the one directly mounted on the docker. Details added to this README.
* Task3 user queries added for practice data.
* Task3 SPARQL queries now do not require subtopic or claimTemplate. Since the fields required in a task3 KB vary with Condition, the required fields are validated by the response validator.
* Task3 validator expanded to perform additional checks.
* Task3 evaluation docker will not process KBs that do not have valid AIF.

## 02/08/2022:
* Section [How to apply the docker to your run in the evaluation setting?](#how-to-apply-the-docker-to-your-run-in-the-evaluation-setting) added to this README
* Following bugs in the Makefile fixed:
  * references to M36 changed to M54
  * IOU thresholds added as expected by the task1 run script

## 02/04/2022:
* a dummy task1 results file is being generated as a placeholder

## 02/03/2022:
* disallowing s3 location as input for task3
* regenerated the Task3 ARF files to make these changes:
  * in outer-claim: add an asessment line for qnode_type, for each qnode_id that the system returned
  * change date format to be YYYY-MM-DD, to be consistent with LDC annotation (probably need to do this earlier in the pipeline)
* Section [Steps in the dockerized pipeline](#steps-in-the-dockerized-pipeline) added to this README

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
