# Confidence aggregation docker for task2 zerohop responses

(Last modified: May 20, 2019)

This document describes how to use the docker to aggregate confidences of task2 zerohop query responses. The layout of this document is as following:

  1. How to build the docker
  2. How to run the docker
  3. How is aggregate confidence computed
  4. Revision history

# How to build the docker

In order to build the docker, assuming that you are inside the following directory:

`dockers/TA2_ZH_ConfidenceAggregation`

Once you are inside the above mentioned directory, you would need to run the following command:

~~~
make build
~~~

# How to run the docker

In order to run the docker, first you would need to change the value of the following variables inside the Makefile:

~~~
HOST_INPUT_DIR
HOST_OUTPUT_DIR
~~~

Once the above change has been made, run the following command to run the docker over the `HOST_INPUT_DIR`

~~~
make run
~~~

Make sure that the value of `HOST_INPUT_DIR` is the absolute path of the directory containing the SPARQL output of a task2 run as produced by `NIST SPARQL query application docker for M18`.

Alternatively, you may run the docker using the following command:

~~~
make run HOST_INPUT_DIR=/absolute/path/to/inputdir HOST_OUTPUT_DIR=/absolute/path/to/outputdir
~~~

# How is aggregate confidence computed

The output of running task2 zerohop queries over a task2-run using `SPARQL query application docker for M18` is a set of files that contains one response per line. Each response contains tab separated values corresponding to the following fields (in that order):

| Column  | Description
---|---------|-------------
1. |       ?docid              |  sourceDocument
2. |        ?query_link_target  |  link target as part of the query
3. |        ?link_target        |  link target in the KB matching ?query_link_target
4. |        ?cluster            |  the ?cluster linked to ?link_target
5. |        ?infj_span          |  informativeJustification span taken from the ?cluster
6. |        ?j_cv               |  confidenceValue of informativeJustification
7. |        ?link_target        |  query reference KB node linked to a ?cluster
8. |        ?link_cv            |  confidenceValue of asserting that ?cluster is the same as reference KB node ?link_target

The default aggregate confidence is the value of `?link_cv`

# Revision history:
### May 20, 2019
  * Initial version
