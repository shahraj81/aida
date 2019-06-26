# How to apply SPARQL queries against a KB using NIST-SPARQL-Evaluation docker (version 2.4)

(Last modified: Jun 25th, 2019)

## Introduction

This document describes how to apply SPARQL queries against a KB using NIST-SPARQL-Evaluation docker as a standalone utility.

This docker does not come with the following but will be required:

1. Free version of GraphDB (version 8.10.1) -- `./docker/AUX-data/graphdb-free-8.10.1-dist.zip`

   NIST-SPARQL-Evaluation docker uses GraphDB as the triple-store for storing (and applying queries against) the KB represented in AIDA Interchange Format. NOTE that the free version comes with the limitation of being able to run no more than two queries in parallel.

   In order to make use of one of GraphDBs paid version (or another free version) place the installer in AUX-data and supply the corresponding values for variables `GRAPHDB_VERSION` and `GRAPHDB_EDITION` to make when invoking `make build`.

   In order to build the docker with the free version, make sure to download the installer from `https://www.ontotext.com/free-graphdb-download/` and place it at: `./docker/AUX-data/graphdb-free-8.10.1-dist.zip`

This docker comes with the following:

1. Local repository configuration file -- `./docker/AUX-data/Local-config.ttl`

   This file is used to create the default repository (named `Local`) for storing the KB.

2. Custom function: GetSpan (version 1.0.1b) -- `./docker/AUX-data/rdf4j-function-getspan-1.0.1b-SNAPSHOT.jar`

   This custom function is used to obtain a standard representation of mention spans across different modalities. This custom function was developed by NIST, and is currently under review by Next Century. After the review, the code will become part of the master branch of VERDI-SPARQL-Evaluation git repository. At that point, you will find a README file inside `custom-functions/rdf4j/rdf4j-function-getspan`. Please refer to this README file (when made available) for more details.

3. Custom function: SuperTypeOf (version 1.0.1b) -- `./docker/AUX-data/rdf4j-function-supertypeof-1.0.1b-SNAPSHOT.jar`

   This custom function is used for applying filter for type matches. This custom function was developed by Next Century, and was modified by NIST. These modifications are currently under review by Next Century. After the review, the modified code will become part of the master branch of VERDI-SPARQL-Evaluation git repository, at which point, you will find a README file inside `custom-functions/rdf4j/rdf4j-function-supertypeof`. Please refer to this README file (when made available) for more details.

4. Custom function: MemberOf (version 1.0.0b) -- `./docker/AUX-data/rdf4j-function-memberof-1.0.0b-SNAPSHOT.jar`

    This custom function is used for applying filter for reference KBID matches in the KB against a set of KBIDs provided by LDC. This custom function was developed by NIST, and is currently under review by Next Century. After the review, the code will become part of the master branch of VERDI-SPARQL-Evaluation git repository. At that point, you will find a README file inside `custom-functions/rdf4j/rdf4j-function-memberof`. Please refer to this README file (when made available) for more details.

5. Custom function: ValidEdge (version 1.0.0b) -- `./docker/AUX-data/rdf4j-function-validedge-1.0.0b-SNAPSHOT.jar`

    This custom function is used for applying filter in TA3 SPARQL queries that check if the subject type is consistent with the edge label. This is determined by splitting the edge_type into two tokens, using underscore (`_`) as the delimiter, and checking if the first token matches strictly with the subject type. This custom function was developed by NIST, and is currently under review by Next Century. After the review, the code will become part of the master branch of VERDI-SPARQL-Evaluation git repository. At that point, you will find a README file inside `custom-functions/rdf4j/rdf4j-function-validedge`. Please refer to this README file (when made available) for more details.

6. VERDI-SPARQL-Evaluation (version 1.0.0) -- `./docker/AUX-data/sparql-evaluation-1.0.0-SNAPSHOT-all.jar`

   The NIST-SPARQL-Evaluation docker is a wrapper written around the version 1.0.0 of VERDI-SPARQL-Evaluation tool developed by Next Century.

   Source code of VERDI-SPARQL-Evaluation can be found at: `https://github.com/NextCenturyCorporation/VERDI-SPARQL-Evaluation`

7. Configuration file required by VERDI-SPARQL-Evaluation -- `./docker/AUX-data/Local-config.properties`

   This configuration file specifies the RDF4J configurations used for applying queries against the `Local` repository.

8. Dockerfile -- `./docker/Dockerfile`

   This file contains the specifications of the NIST-SPARQL-Evaluation docker.

9. Makefile -- `./docker/Makefile`

   The Makefile for building and running the docker.

10. scripts/Makefile -- `./docker/scripts/Makefile`

   The Makefile for running queries against a KB using `VERDI-SPARQL-Evaluation`.

11. Example data -- `./M18-data`

   The docker comes with the following:

   (a) Example runs (or submissions) -- `./M18-data/runs`. This includes example for all the tasks: task1, task2 and task3 runs.

   (b) Example queries -- `./M18-data/queries`. Queries have been generated from prevailing theories found in LDC2019E07_AIDA_Phase_1_Evaluation_Practice_Topic_Annotations_V6.0. Please refer to M18-data/queries/README for details on changes to queries.

   (c) Example output -- `./M18-data/example-output`

## How to build the docker

#### Using the default (free) version of GraphDB

As of the last modified date (see above), the latest free version of GraphDB is 8.10.1 which will be used by the docker by default. In order to build the docker using the default (free) version of GraphDB:

1. download the installer from `https://www.ontotext.com/free-graphdb-download/`,
2. place it at: `./docker/AUX-data/graphdb-free-8.10.1-dist.zip`, and
3. run the following command(s):

~~~
cd docker
make build
~~~

#### Using paid version (or another free version) version of GraphDB

In order to build the docker with either a paid version of GraphDB or a version different from the one used by default, you would need to

1. Download the paid version of GraphDB `graphdb-[otheredition]-[otherversion]-dist.zip` and place it inside `docker/AUX-data/`, and

2. Run the following command(s):

~~~
cd docker
make build GRAPHDB_EDITION=otheredition GRAPHDB_VERSION=otherversion
~~~

## How to run the docker

#### Running example queries against example run(s)

In order to apply example queries over example runs (or submissions), run the following commands:

~~~
make run-all
~~~

You can find the output at `./M18-data/output`. In order to verify that the docker worked as expected, you may want to compare the content of `./M18-data/output` with `./M18-data/example-output`.

#### Running example queries against your own run

In order to run the example queries against your own run (or submission), you may run the `make run` command, as shown below, and supply the following:

Parameter | Description
--- | ---
`HOST_RUN_DIR` | the directory containing the task1 KBs or task2 KB
`HOST_QUERIES_DIR` | the directory containing SPARQL query files (\*.rq files) for a given query type
`HOST_OUTPUT_DIR` | the directory where output will be written

~~~
make run \
      HOST_RUN_DIR=/path/to/your/run \
      HOST_QUERIES_DIR=/path/to/queries \
      HOST_OUTPUT_DIR=/path/to/output \
~~~

## Revision history
#### version 1.0
  * Initial version containing only example queries

#### version 2.0
  * More example queries added

#### version 2.1
  * Example KBs modified to fix validation errors

#### version 2.2
  * In order to support matching against ambiguous nodes that were split in reference KB
    * Custom function `memberOf` added
    * TA2 queries modified to make use of custom function memberOf
  * Example KBs modified to fix validation errors

#### version 2.3
  * TA1 and TA2 graph queries had a bug in where SPARQL was looking up for confidence value of justification of an argument assertion. Originally, the confidence associated with an argument assertion was mistakenly extracted and used as the confidence of the justification of the argument assertion. The queries that come along with this version are generated from the new template of queries.
  * Example TA3 hypothesis added
  * TA3 graph SPARQL query added
  * Custom function `validEdge` added. This custom function is only used in TA3 graph SPARQL query.

#### version 2.3.1
  * Added a note that the docker does not come with the installer of the free version of GraphDB.
  * Added the docker and M18-data to the repository

#### version 2.4
  * Default free version used by the docker updated to `graphdb-free-8.10.1`.
  * This version contains queries generated from prevailing theories found in LDC2019E07_AIDA_Phase_1_Evaluation_Practice_Topic_Annotations_V6.0.
  * Refer to M18-data/queries/README for details on changes to queries.
