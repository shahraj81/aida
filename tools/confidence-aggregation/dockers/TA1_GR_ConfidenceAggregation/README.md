# Confidence aggregation docker for Task1 Graph query responses

(Last modified: May 21, 2019)

This document describes how to use the docker to aggregate confidences of Task1 Graph query responses. The layout of this document is as following:

  1. How to build the docker
  2. How to run the docker
  3. How is aggregate confidence computed
  4. Output of the docker
  5. Revision history

# How to build the docker

In order to build the docker, first change to the following directory:

`dockers/TA1_GR_ConfidenceAggregation`

and then run the following command:

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

Make sure that the value of `HOST_INPUT_DIR` is the absolute path of the directory containing the SPARQL output of a Task1 run as produced by `NIST SPARQL query application docker for M18`.

Alternatively, you may run the docker using the following command:

~~~
make run HOST_INPUT_DIR=/absolute/path/to/inputdir HOST_OUTPUT_DIR=/absolute/path/to/outputdir
~~~

# How is aggregate confidence computed

The output of running Task1 Graph queries over a Task1-run using `SPARQL query application docker for M18` is a set of files that contains one response per line. Each response contains tab separated values corresponding to the following fields (in that order):

|     | Column            | Description |
|-----|-------------------|-------------|
| 1.  | ?docid            |  sourceDocument |
| 2.  | ?edge_type_q      |  edge type in the query |
| 3.  | ?edge_type        |  edge type in response matching the edge type in query |
| 4.  | ?object_cluster   |  object cluster |
| 5.  | ?objectmo         |  member of object cluster |
| 6.  | ?oinf_j_span      |  informativeJustification of the member of object cluster |
| 7.  | ?subject_cluster  |  subject cluster |
| 8.  | ?subjectmo        |  member of subject cluster |
| 9.  | ?ej_span          |  CompoundJustification span(s) for argument assertion |
| 10. | ?oinf_j_cv        |  confidence of object informativeJustification |
| 11. | ?obcm_cv          |  cluster membership confidence of the object |
| 12. | ?edge_cv          |  confidence of a compound justification for the argument assertion |
| 13. | ?sbcm_cv          |  cluster membership confidence of the subject |

The default aggregate confidence of a ?cluster is computed as the product of the following columns:

|     | Column            | Description |
|-----|-------------------|-------------|
| 1.  | ?oinf_j_cv        |  confidence of object informativeJustification |
| 2.  | ?obcm_cv          |  cluster membership confidence of the object |
| 3.  | ?edge_cv          |  confidence of a compound justification for the argument assertion |
| 4.  | ?sbcm_cv          |  cluster membership confidence of the subject |

Note that the Task1 Graph SPARQL query does not extract informativeJustification of member of ?subject_cluster as it is not needed by LDC for assessment.

# Output of the docker

For each file in the input directory, the docker produces an output file. For each line in the input file, the docker computes aggregate confidence values, and outputs the same columns as the SPARQL output fill, plus two additional columns (rank and aggregate edge justification confidence value) appended at the end.

The docker also filters the contents of the SPARQL output file such that for each unique edge (having unique combination of subject cluster ID, edge label, and object cluster ID), there is at most one line in the docker output file. This is done by keeping the response that has the highest aggregate confidence value among all the responses corresponding to the edge.

The filtered responses are then ranked by ordering based on aggregate confidence values such that the response with highest aggregate confidence value is on the top with rank=1. Note that ties are broken arbitrarily.

The output file contains the following columns:

|     | Column            | Description |
|-----|-------------------|-------------|
| 1.  | ?docid            |  sourceDocument |
| 2.  | ?edge_type_q      |  edge type in the query |
| 3.  | ?edge_type        |  edge type in response matching the edge type in query |
| 4.  | ?object_cluster   |  object cluster |
| 5.  | ?objectmo         |  member of object cluster |
| 6.  | ?oinf_j_span      |  informativeJustification of the member of object cluster |
| 7.  | ?subject_cluster  |  subject cluster |
| 8.  | ?subjectmo        |  member of subject cluster |
| 9.  | ?ej_span          |  CompoundJustification span(s) for argument assertion |
| 10. | ?oinf_j_cv        |  confidence of object informativeJustification |
| 11. | ?obcm_cv          |  cluster membership confidence of the object |
| 12. | ?edge_cv          |  confidence of a compound justification for the argument assertion |
| 13. | ?sbcm_cv          |  cluster membership confidence of the subject |
| 14. | ?ag_cv            |  aggregate confidence value
| 15. | ?rank             |  the rank of based on the aggregate confidence value computed as described above

# Revision history:
### May 20, 2019
  * Initial version

### May 21, 2019
  * Fixed the formatting of tables
  * Description in section `Output of the docker` revised
