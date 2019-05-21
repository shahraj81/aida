# Confidence aggregation docker for task2 graph responses

(Last modified: May 21, 2019)

This document describes how to use the docker to aggregate confidences of task2 graph query responses. The layout of this document is as following:

  1. How to build the docker
  2. How to run the docker
  3. How is aggregate confidence computed
  4. Output of the docker
  5. Revision history

# How to build the docker

In order to build the docker, assuming that you are inside the following directory:

`dockers/TA2_GR_ConfidenceAggregation`

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

The output of running task2 graph queries over a task2-run using `SPARQL query application docker for M18` is a set of files that contains one response per line. Each response contains tab separated values corresponding to the following fields (in that order):


| | Column | Description |
| ---|---------|-------------|
| 1. |        ?docid            |  sourceDocument|
| 2. |        ?edge_type_q      |  edge type in the query|
| 3. |        ?edge_type        |  edge type in response matching the edge type in query|
| 4. |        ?olink_target_q   |  reference KB node given in query|
| 5. |        ?olink_target     |  reference KB node linked to the object of the edge matching ?olink_target_q|
| 6. |        ?object_cluster   |  object cluster|
| 7. |        ?objectmo         |  member of object cluster|
| 8. |        ?oinf_j_span      |  informativeJustification of the member of object cluster|
| 9. |        ?subject_cluster  |  subject cluster|
| 10. |        ?subjectmo        |  member of subject cluster|
| 11. |        ?ej_span          |  CompoundJustification span(s) for argument assertion|
| 12. |        ?orfkblink_cv     |  confidence of linking the object to the query reference KB ID|
| 13. |        ?oinf_j_cv        |  confidence of object informativeJustification|
| 14. |        ?obcm_cv          |  cluster membership confidence of the object|
| 15. |        ?edge_cv          |  confidence of a compound justification for the argument assertion|
| 16. |        ?sbcm_cv          |  cluster membership confidence of the subject|

The default aggregate confidence of a ?cluster is computed as the product of the following columns:

| | Column  | Description|
|---|---------|-------------|
| 1. |        ?orfkblink_cv     |  confidence of linking the object to the query reference KB ID|
| 2. |        ?oinf_j_cv        |  confidence of object informativeJustification|
| 3. |        ?obcm_cv          |  cluster membership confidence of the object|
| 4. |        ?edge_cv          |  confidence of a compound justification for the argument assertion|
| 5. |        ?sbcm_cv          |  cluster membership confidence of the subject|

Note that the task2 graph SPARQL query does not extract informativeJustification of ?subjectmo as it is not needed by LDC for assessment.

# Output of the docker

For each file in the input directory, the docker produces an output file. For each line in the input file, the docker computes aggregate confidence values (as described above), and outputs the same columns as the SPARQL output , plus two additional columns (rank and aggregate edge justification confidence value) appended at the end.

The docker ranks the subject clusters using aggregate confidence value, and (for each cluster) filters possible assessment items to select k=1 assessment items for the cluster by selecting the response with the highest aggregate confidence value among all corresponding responses. Each line in the docker output file must have a rank that is unique across the entire output file of the docker.

The output file contains the following columns:

| | Column | Description |
| ---|---------|-------------|
| 1. |        ?docid            |  sourceDocument|
| 2. |        ?edge_type_q      |  edge type in the query|
| 3. |        ?edge_type        |  edge type in response matching the edge type in query|
| 4. |        ?olink_target_q   |  reference KB node given in query|
| 5. |        ?olink_target     |  reference KB node linked to the object of the edge matching ?olink_target_q|
| 6. |        ?object_cluster   |  object cluster|
| 7. |        ?objectmo         |  member of object cluster|
| 8. |        ?oinf_j_span      |  informativeJustification of the member of object cluster|
| 9. |        ?subject_cluster  |  subject cluster|
| 10. |        ?subjectmo        |  member of subject cluster|
| 11. |        ?ej_span          |  CompoundJustification span(s) for argument assertion|
| 12. |        ?orfkblink_cv     |  confidence of linking the object to the query reference KB ID|
| 13. |        ?oinf_j_cv        |  confidence of object informativeJustification|
| 14. |        ?obcm_cv          |  cluster membership confidence of the object|
| 15. |        ?edge_cv          |  confidence of a compound justification for the argument assertion|
| 16. |        ?sbcm_cv          |  cluster membership confidence of the subject|
| 17. |        ?ag_cv          |  aggregate confidence value|
| 18. |        ?rank          | the rank of based on the aggregate confidence value computed as described above|

# Revision history:
### May 20, 2019
  * Initial version

### May 21, 2019
  * Section `Output of the docker` added
  * Fixed formatting of the tables
