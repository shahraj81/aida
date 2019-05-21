# Confidence aggregation docker for Task2 Zerohop responses

(Last modified: May 21, 2019)

This document describes how to use the docker to aggregate confidences of Task2 Zerohop query responses. The layout of this document is as following:

  1. How to build the docker
  2. How to run the docker
  3. How is aggregate confidence computed
  4. Output of the docker
  5. Revision history

# How to build the docker

In order to build the docker, first change to the following directory:

`dockers/TA2_ZH_ConfidenceAggregation`

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

Make sure that the value of `HOST_INPUT_DIR` is the absolute path of the directory containing the SPARQL output of a task2 run as produced by `NIST SPARQL query application docker for M18`.

Alternatively, you may run the docker using the following command:

~~~
make run HOST_INPUT_DIR=/absolute/path/to/inputdir HOST_OUTPUT_DIR=/absolute/path/to/outputdir
~~~

# How is aggregate confidence computed

The output of running Task2 Zerohop queries over a Task2-run using `SPARQL query application docker for M18` is a set of files that contains one response per line. Each response contains tab separated values corresponding to the following fields (in that order):

|    | Column  | Description |
|----|---------|-------------|
| 1. | ?docid              |  sourceDocument |
| 2. | ?query_link_target  |  link target as part of the query |
| 3. | ?link_target        |  link target in the KB matching ?query_link_target |
| 4. | ?cluster            |  the ?cluster linked to ?link_target |
| 5. | ?infj_span          |  informativeJustification span taken from the ?cluster |
| 6. | ?j_cv               |  confidenceValue of informativeJustification |
| 7. | ?link_target        |  query reference KB node linked to a ?cluster |
| 8. | ?link_cv            |  confidenceValue of asserting that ?cluster is the same as reference KB node ?link_target |

The default aggregate confidence is the value of `?link_cv`

# Output of the docker

For each file in the input directory, the docker produces an output file. For each line in the input file, the docker computes aggregate confidence values and outputs a ranking of all the entity clusters in the SPARQL output file.

Each cluster in the SPARQL output file appears exactly once in the docker output file. The clusters are ranked by ordering based on aggregate confidence values such that the cluster with highest aggregate confidence value is on the top with rank=1. Note that ties are broken arbitrarily.

The output file contains the following columns:

|    | Column       | Description |
| ---|--------------|------------- |
| 1. |   ?cluster    |  a ?cluster in the SPARQL output file |
| 2. |   ?rank       |  the rank of ?cluster using the aggregate confidence value computed as described above |

# Revision history:
### May 20, 2019
  * Initial version

### May 21, 2019
  * Fixed the formatting of tables
  * Description in section `Output of the docker` revised
