# Confidence aggregation docker for task1 graph responses

(Last modified: May 20, 2019)

This document describes how to use the docker to aggregate confidences of task1 graph query responses. The layout of this document is as following:

  1. How to build the docker
  2. How to run the docker
  3. How is aggregate confidence computed
  4. Revision history

# How to build the docker

In order to build the docker, assuming that you are inside the following directory:

`dockers/TA1_GR_ConfidenceAggregation`

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

Make sure that the value of `HOST_INPUT_DIR` is the absolute path of the directory containing the SPARQL output of a task1/task2 run as produced by `NIST SPARQL query application docker for M18`.

Alternatively, you may run the docker using the following command:

~~~
make run HOST_INPUT_DIR=/absolute/path/to/inputdir HOST_OUTPUT_DIR=/absolute/path/to/outputdir
~~~

# How is aggregate confidence computed

The output of running task1 graph queries over a task1-run using `SPARQL query application docker for M18` is a set of files that contains one response per line. Each response contains tab separated values corresponding to the following fields (in that order):

| Column  | Description
---|---------|-------------
1. |        ?docid         |  sourceDocument |
2. |        ?edge_type_q   |  edge type in the query |
3. |        ?edge_type     |  edge type in response matching the edge type in query |
4. |        ?object_cluster  |  object cluster |
5. |        ?objectmo      |  member of object cluster |
6. |        ?oinf_j_span   |  informativeJustification of the member of object cluster |
7. |        ?subject_cluster  |  subject cluster |
8. |        ?subjectmo     |  member of subject cluster |
9. |        ?ej_span       |  CompoundJustification span(s) for argument assertion |
10. |        ?oinf_j_cv     |  confidence of object informativeJustification |
11. |        ?obcm_cv       |  cluster membership confidence of the object |
12. |        ?edge_cv       |  confidence of a compound justification for the argument assertion |
13. |        ?sbcm_cv       |  cluster membership confidence of the subject |

The default aggregate confidence of a ?cluster is computed as the product of the following columns:

| Column  | Description
---|---------|-------------
1. |        ?oinf_j_cv     |  confidence of object informativeJustification |
2. |        ?obcm_cv       |  cluster membership confidence of the object |
3. |        ?edge_cv       |  confidence of a compound justification for the argument assertion |
4. |        ?sbcm_cv       |  cluster membership confidence of the subject |

Note that the task1 graph SPARQL query does not extract informativeJustification of member of ?subject_cluster as it is not needed by LDC for assessment.

# Revision history:
### May 20, 2019
  * Initial version
