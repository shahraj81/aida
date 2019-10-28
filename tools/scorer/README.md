# Introduction

October 28, 2019

This document describes:

	1. Usage of the Scorer,
	2. How to generate the official scores, 
	3. How to read scorer output,
	4. How to read the debug file,
	5. Example submission and corresponding scores, and
	6. Revision history

# Usage of the Scorer

~~~
AIDA-Score-MASTER.pl:  Score SPARQL-based output files

Usage: AIDA-Score-MASTER.pl {-switch {-switch ...}} coredocs docid_mappings sentence_boundaries images_boundingboxes keyframes_boundingboxes queries queries_dtd queries_xml salient_edges assessments rundir cadir intermediate output

Legal switches are:
  -error_file <value>  Specify a file to which error output should be redirected
                         (Default = STDERR).
  -help                Show help
  -runid <value>       Run ID of the system being scored (Default = system).
  -strategy <value>    Scoring strategy? (Default = default).
  -version             Print version number and exit
parameters are:
  coredocs                 List of core documents to be included in the pool
                             (Required).
  docid_mappings           DocumentID to DocumentElementID mappings (Required).
  sentence_boundaries      File containing sentence boundaries (Required).
  images_boundingboxes     File containing image bounding boxes (Required).
  keyframes_boundingboxes  File containing keyframe bounding boxes (Required).
  queries                  File containing queryids to be pooled. (Required).
  queries_dtd              DTD file corresponding to the XML file containing
                             queries (Required).
  queries_xml              XML file containing queries (Required).
  salient_edges            File containing edges sailent to prevailing theories
                             or 'none' (Required).
  assessments              Assessment package as receieved from LDC (Required).
  rundir                   Run directory containing validated SPARQL output
                             files (Required).
  cadir                    Directory containing confidence aggregation output
                             (Required).
  intermediate             Specify a directory where intermediate data can be
                             written; the directory should not exist (Required).
  output                   Output file (Required).
~~~

# How to generate the official scores

#### Scoring task1 class responses

In order to score task1 class responses, you may run the following command

~~~
 perl AIDA-Score-MASTER.pl \
    -error_file SomeTA1CLRun.score.errlog \
    -runid SomeTA1CLRun \
    M18-AUX-evaluation-data/LDC2019E42.coredocs-18.txt \
    M18-AUX-evaluation-data/LDC2019E42.parent_children.tsv \
    M18-AUX-evaluation-data/LDC2019E42.sentence_boundaries.txt \
    M18-AUX-evaluation-data/LDC2019E42.image_boundaries.txt \
    M18-AUX-evaluation-data/LDC2019E42.keyframe_boundaries.txt \
    M18-AUX-evaluation-data/task1_class_queryids.txt \
    M18-AUX-evaluation-data/class_query.dtd \
    M18-AUX-evaluation-data/task1_class_queries.xml \
    none \
    /path/to/LDC2019R30_AIDA_Phase_1_Assessment_Results_V5.0/ \
    /path/to/SomeTA1CLRun/SPARQL-VALID-output/ \
    /path/to/SomeTA1CLRun/SPARQL-CA-output/ \
    /path/to/intermediate-data/SomeTA1CLRun/ \
    SomeTA1CLRun.score.txt
~~~

#### Scoring task1 graph responses

In order to score task1 graph responses, you may run the following command

~~~
  perl AIDA-Score-MASTER.pl \
    -error_file SomeTA1GRRun.score.errlog \
    -runid SomeTA1GRRun \
    M18-AUX-evaluation-data/LDC2019E42.coredocs-26.txt \
    M18-AUX-evaluation-data/LDC2019E42.parent_children.tsv \
    M18-AUX-evaluation-data/LDC2019E42.sentence_boundaries.txt \
    M18-AUX-evaluation-data/LDC2019E42.image_boundaries.txt \
    M18-AUX-evaluation-data/LDC2019E42.keyframe_boundaries.txt \
    M18-AUX-evaluation-data/task1_graph_queryids.txt \
    M18-AUX-evaluation-data/graph_query.dtd \
    M18-AUX-evaluation-data/task1_graph_queries.xml \
    none \
    /path/to/LDC2019R30_AIDA_Phase_1_Assessment_Results_V5.0/ \
    /path/to/SomeTA1GRRun/SPARQL-VALID-output/ \
    /path/to/SomeTA1GRRun/SPARQL-CA-output/ \
    /path/to/intermediate-data/SomeTA1GRRun/ \
    SomeTA1GRRun.score.txt
~~~

#### Scoring task2 zerohop responses

In order to score task2 zerohop responses, you may run the following command

~~~
  perl AIDA-Score-MASTER.pl \
    -error_file SomeTA2ZHRun.score.errlog \
    -runid SomeTA2ZHRun \
    M18-AUX-evaluation-data/LDC2019E42.coredocs-all.txt \
    M18-AUX-evaluation-data/LDC2019E42.parent_children.tsv \
    M18-AUX-evaluation-data/LDC2019E42.sentence_boundaries.txt \
    M18-AUX-evaluation-data/LDC2019E42.image_boundaries.txt \
    M18-AUX-evaluation-data/LDC2019E42.keyframe_boundaries.txt \
    M18-AUX-evaluation-data/task2_zerohop_queryids.txt \
    M18-AUX-evaluation-data/zerohop_query.dtd \
    M18-AUX-evaluation-data/task2_zerohop_queries.xml \
    none \
    /path/to/LDC2019R30_AIDA_Phase_1_Assessment_Results_V5.0/ \
    /path/to/SomeTA2ZHRun/SPARQL-VALID-output/ \
    /path/to/SomeTA2ZHRun/SPARQL-CA-output/ \
    /path/to/intermediate-data/SomeTA2ZHRun/ \
    SomeTA2ZHRun.score.txt
~~~

#### Scoring task2 graph responses

The scorer generates the following two variants of scores for task2 graph responses:

	1. Strategy 1,
	2. Strategy 2.

In order to score task2 graph responses, you may run the following commands:

###### Strategy 1:

~~~
  perl AIDA-Score-MASTER.pl \
    -error_file SomeTA2GRRunStrategy1.score.errlog \
    -runid SomeTA2GRRun \
    -strategy strategy1 \
    M18-AUX-evaluation-data/LDC2019E42.coredocs-26.txt \
    M18-AUX-evaluation-data/LDC2019E42.parent_children.tsv \
    M18-AUX-evaluation-data/LDC2019E42.sentence_boundaries.txt \
    M18-AUX-evaluation-data/LDC2019E42.image_boundaries.txt \
    M18-AUX-evaluation-data/LDC2019E42.keyframe_boundaries.txt \
    M18-AUX-evaluation-data/task2_graph_queryids.txt \
    M18-AUX-evaluation-data/graph_query.dtd \
    M18-AUX-evaluation-data/task2_graph_queries.xml \
    M18-AUX-evaluation-data/salient_edges.txt \
    /path/to/LDC2019R30_AIDA_Phase_1_Assessment_Results_V5.0/ \
    /path/to/SomeTA2GRRun/SPARQL-VALID-output/ \
    /path/to/SomeTA2GRRun/SPARQL-CA-output/ \
    /path/to/intermediate-data/SomeTA2GRRun/ \
    SomeTA2GRRunStrategy1.score.txt
~~~

###### Strategy 2:

~~~
  perl AIDA-Score-MASTER.pl \
    -error_file SomeTA2GRRunStrategy2.score.errlog \
    -runid SomeTA2GRRun \
    -strategy strategy2 \
    M18-AUX-evaluation-data/LDC2019E42.coredocs-26.txt \
    M18-AUX-evaluation-data/LDC2019E42.parent_children.tsv \
    M18-AUX-evaluation-data/LDC2019E42.sentence_boundaries.txt \
    M18-AUX-evaluation-data/LDC2019E42.image_boundaries.txt \
    M18-AUX-evaluation-data/LDC2019E42.keyframe_boundaries.txt \
    M18-AUX-evaluation-data/task2_graph_queryids.txt \
    M18-AUX-evaluation-data/graph_query.dtd \
    M18-AUX-evaluation-data/task2_graph_queries.xml \
    M18-AUX-evaluation-data/salient_edges.txt \
    /path/to/LDC2019R30_AIDA_Phase_1_Assessment_Results_V5.0/ \
    /path/to/SomeTA2GRRun/SPARQL-VALID-output/ \
    /path/to/SomeTA2GRRun/SPARQL-CA-output/ \
    /path/to/intermediate-data/SomeTA2GRRun/ \
    SomeTA2GRRunStrategy2.score.txt
~~~

# Understanding the output

## Task1 class scores

| Column        | Description   |
| ------------- | ------------- |
| GT            | Number of distict KB ID or NIL ID (Column 9 in assessment file) <br>- each correct NIL singleton is counted as distinct |
| Sub           | Number of clusters submitted |
| Pooled        | Number of clusters pooled |
| Correct       | Number of correct pooled clusters (Pre-policy) |
| Dup           | Number of correct pooled clusters that had the same KB ID or NIL ID as of another correct pooled cluster (Pre-policy) <br>- each duplicate response was considered Wrong as Post-policy assessment |
| Incrct        | Number of pooled clusters that were assessed to be incorrect (Pre-policy) |
| Cntd          | Number of pooled clusters counted towards scores <br>- Cntd = Right + Wrong |
| Right         | Number of pooled clusters that were assessed correct and were not duplicate (Post-policy) |
| Wrong         | Number of pooled clusters that were either assessed as incorrect, or were duplicate (Post-policy) |
| Ignrd         | Number of pooled clusters that were ignored (Post-policy) |
| AP-B          | AP score where ties are broken by ranking all Right responses above all the Wrong response |
| AP-W          | AP score where ties are broken by ranking all Wrong responses above all the Right response |
| AP-T          | AP score where ties are broken as in TRECEVAL (Sort by aggregate confidence and then by mention span and then by cluster_id) |

## Task2 zerohop scores

| Column        | Description   |
| ------------- | ------------- |
| GT            | Number of distinct documents containing a mention of the entity in query  |
| Sub           | Number of distinct documents submitted (response with the highest JUSTIFICATION_CONFIDENCE is selected if multiple responses were provided from the document; if KBs were validated this would be unnecessary; also in case of a tie one response is selected arbitrarily) |
| Pooled        | Number of responses pooled |
| Correct       | Number of correct responses (Pre-policy) |
| Dup           | Number of correct responses that appeared twice for some reason (Pre-policy) <br>- we anticipate this to be zero all the time, under the current scoring paradigm |
| Incrct        | Number of responses assessed to be incorrect (Pre-policy) |
| Cntd          | Number of responses counted towards scores <br>- Cntd = Right + Wrong |
| Right         | Number of pooled responses assessed as correct (Post-policy) |
| Wrong         | Number of pooled responses assessed as incorrect (Post-policy) |
| Ignrd         | Number of pooled responses that were ignored (Post-policy) |
| AP-B          | AP score where ties are broken by ranking all Right responses above all the Wrong response |
| AP-W          | AP score where ties are broken by ranking all Wrong responses above all the Right response |
| AP-T          | AP score where ties are broken as in TRECEVAL (Sort by aggregate confidence and then by mention span) |

## Task1 graph scores

### Strategy 1

| Column | Description   |
| ------------- | ------------- |
| GTA           | Number of distinct edge equivalence classes in ground truth (Note: every instance of NIL subject or object equivalence class is considered to be distinct as it represents a singleton class) |
| GT            | Number of distinct edge equivalence classes in ground truth counted towards score (GT = min(GTA,depth)) |
| Sub           | Number of responses (unique combination of subject cluster ID, predicate, and object cluster ID) that were found in confidence aggregation output |
| Pooled        | Number of responses that were included in the pool (these should be the top C responses by their rank in confidence aggregation output) |
| Correct       | Number of responses where the predicate justification is correct (Pre-policy) |
| PJLnkabl2O    | Number of responses where the predicate justification is correct AND the object in predicate justification is linkable to the object justification (Pre-policy) |
| Dup           | Number of responses where the predicate justification is correct AND the object in predicate justification is linkable to the object justification  AND the object is linkable to query entity, but credit was already given for the real world edge in another pooled response; these will be ignored for the purpose of computing precision (system failed to cluster multiple mentions of the same real-world subject and object) |
| Incrct        | Number of responses where the predicate justifiation is incorrect (Pre-policy) |
| Cntd          | Number of responses counted towards scores <br>- Cntd = Right + Wrong |
| Right         | Number of pooled responses counted as correct (Post-policy) <br>- These included responses that met all of the following properties:<br>&nbsp;&nbsp;&nbsp;&nbsp;- predicate justification is judged to be correct by assessors,<br>&nbsp;&nbsp;&nbsp;&nbsp;- the mention of object in predicate justification was linkable to the object justification, and<br>&nbsp;&nbsp;&nbsp;&nbsp;- credit for correct edge equivalence class was not already given earlier (i.e. not duplicate) |
| Wrong         | Number of pooled responses counted as incorrect (Post-policy) <br>- These included responses that failed to meet all of the following properties:<br>&nbsp;&nbsp;&nbsp;&nbsp;- predicate justification is judged to be correct by assessors, and<br>&nbsp;&nbsp;&nbsp;&nbsp;- the mention of object in predicate justification was linkable to the object justification |
| Ignrd         | Number of pooled responses that were ignored (Post-policy) <br>- Ignrd = Dup<br>- Ignrd = Pooled - Cntd |
| Prec          | Precision of responses that were Right (Prec = Right/Cntd)|
| Recall        | Recall of responses that were Right (Recall = Right/GT) |
| F1            | F1 of Prec and Recall |

## Task2 graph scores

### Strategy 1

| Column header | Description   |
| ------------- | ------------- |
| GTA(1a)       | Number of distinct equivalence classes of the subject in ground truth (Note: every instance of NIL subject equivalence class is considered to be distinct as it represents a singleton class) |
| GT(1a)        | Number of distinct equivalence classes in ground truth counted towards score (GT(1a) = min(GTA(1a),depth)) |
| GTA(1b)       | Number of distinct edges in LDC's prevailing theories, where the prevailing theory edge has the same predicate as the query and the object of the edge is linkable to the query entity |
| GT(1b)        | Number of distinct edges in LDC's previaling theories that are counted towards score (GT(1b) = min(GTA(1b),depth)) |
| Sub           | Number of responses (different subject cluster IDs) that were found in confidence aggregation output |
| Pooled        | Number of responses that were included in the pool (these should be the top C responses by their rank in confidence aggregation output) |
| Correct       | Number of responses where the predicate justification is correct (Pre-policy) |
| PJLnkabl2O    | Number of responses where the predicate justification is correct AND the object in predicate justification is linkable to the object justification (Pre-policy) |
| OLnkabl2QE    | Number of responses where the predicate justification is correct AND the object in predicate justification is linkable to the object justification  AND the object is linkable to query entity |
| Dup           | Number of responses where the predicate justification is correct AND the object in predicate justification is linkable to the object justification  AND the object is linkable to query entity, but credit was already given for the real world subject entity in another pooled response; these will be ignored for the purpose of computing precision (system failed to cluster multiple mentions of the same real-world subject) |
| Incrct        | Number of responses where the predicate justifiation is incorrect (Pre-policy) |
| Cntd          | Number of responses counted towards scores<br>- Cntd = Right + Wrong |
| Right         | Number of pooled responses counted as correct (Post-policy)<br>- These included responses that met all of the following properties:<br>&nbsp;&nbsp;&nbsp;&nbsp;- predicate justification is judged to be correct by assessors,<br>&nbsp;&nbsp;&nbsp;&nbsp;- the mention of object in predicate justification was linkable to the object justification,<br>&nbsp;&nbsp;&nbsp;&nbsp;- the object was linkable to query entity, and<br>&nbsp;&nbsp;&nbsp;&nbsp;- credit for correct edge equivalence class was not already given earlier (i.e. not duplicate) |
| Wrong         | Number of pooled responses counted as incorrect (Post-policy)<br>- These included responses that failed to meet all of the following properties:<br>&nbsp;&nbsp;&nbsp;&nbsp;- predicate justification is judged to be correct by assessors,<br>&nbsp;&nbsp;&nbsp;&nbsp;- the mention of object in predicate justification was linkable to the object justification, and<br>&nbsp;&nbsp;&nbsp;&nbsp;- the object was linkable to query entity |
| Ignrd         | Number of pooled responses that were ignored (Post-policy)<br>- Ignrd = Dup<br>- Ignrd = Pooled - Cntd |
| Salient       | Number of Right responses (edges) that are salient to LDC's prevailing theories<br>- the edge (subject equivalence class, predicate, object equivalence class) is in one of the prevailing theories (and object is linkable to the query entity) |
| Prec(1a)      | Precision of responses that were Right (Prec(1a) = Right/Cntd) |
| Recall(1a)    | Recall of responses that were Right (Recall(1a) = Right/GT(1a)) |
| F1(1a)        | F1 of Prec(1a) and Recall(1a) |
| Recall(1b)    | Recall of salient edges (Recall(1b)=Salient/GT(1b)) |

### Strategy 2

| Column header | Description   |
| ------------- | ------------- |
| FrameID       | Frame ID<br>- event (or relation) KE in a particular prevailing theory<br>- granularity of the event or relation<br>&nbsp;&nbsp;&nbsp;&nbsp;- FG = Fine grained (type.subtype.subsubtype)<br>&nbsp;&nbsp;&nbsp;&nbsp;- CG = Coarse grained (type.subtype) |
| RunID         | Run ID |
| NumQueries    | Number of edges in the frame (where each argument is linkable to the reference KB); each edge in the frame is associated with exactly one TA2 edge query |
| FrameValue    | the maximum number of unique edges in the submitted event/relation KEs that are Right AND that have the same global KB ID for the subject<br>- an edge is Right if<br>&nbsp;&nbsp;&nbsp;&nbsp;- predicate justification is judged to be correct by assessors, <br>&nbsp;&nbsp;&nbsp;&nbsp;- the mention of object in predicate justification was linkable to the object justification, and<br>&nbsp;&nbsp;&nbsp;&nbsp;- the object was linkable to query entity |
| FrameRecall   | FrameValue/NumQueries (except if FrameValue is 0, then FrameRecall is 0) |

# Understanding the debug/log file

In this section, we highlight different types of entries in the log file:

## Task1 class scores

### AP_SUBMISSION_LINE

These entries show what ranking was used for computing AP where ties are broken using the following strategies:
	1. BESTCASE (see AP-B above)
	2. WORSECASE (see AP-W above)
	3. TRECEVAL (see AP-T above)

These entries contain 13 values in different columns as shown:

    - Column # 1: DEBUG_INFO
    - Column # 2: AP_SUBMISSION_LINE
    - Column # 3: BESTCASE or WORSTCASE or TRECEVAL
    - Column # 4: Query ID
    - Column # 5: Document ID
    - Column # 6: Mention span
    - Column # 7: Rank
    - Column # 8: Score
    - Column # 9: RunID
    - Column # 10: RIGHT | WRONG
    - Column # 11: KB ID | NIL ID | N/A (N/A when the response cluster was assessed to be incorrect)
    - Column # 12: Cluster ID
    - Column # 13: Filename and line number where response was found

### ASSESSMENT_INFO

These entries list all the responses read from the validated SPARQL output file along with corresponding confidence aggregation file; and show assessment information corresponding to the response.

These entries contain 10 values in different columns as shown:

    - Column # 1: DEBUG_INFO
    - Column # 2: ASSESSMENT_INFO
    - Column # 3: Query ID
    - Column # 4: Document ID
    - Column # 5: Mention span
    - Column # 6: Cluster ID
    - Column # 7: Aggregated confidence value
    - Column # 8: KB ID or NIL ID or N/A (N/A when the response cluster was assessed to be incorrect)
    - Column # 9: Pre-policy assessment information and response categorization
    - Column # 10: Post-policy response categorization

Following is the list of categories corresponding to column # 9:

    - CORRECT: Response was assessed to be correct
    - INCORRECT: Response was assessed to be incorrect
    - POOLED: Response was included in the pool
    - REDUNDANT: Response was correct but also redundant because of another correct response with the same KB ID submitted
    - SUBMITTED: Was the top ranked response from the cluster
    - SUBMITTED-A: All responses
    - SUBMITTED-B: Response submitted for the best matching cluster(s)
    - SUBMITTED-C: Response corresponds to document included in the coredocs

Responses were found to have one of the following group of categories:

    - NOT-CONSIDERED,SUBMITTED-A,SUBMITTED-C: The response corresponds to document included in the coredocs but did not contain the best matching cluster.
    - NOT-CONSIDERED,SUBMITTED-A,SUBMITTED-B,SUBMITTED-C: The response corresponds to best matching cluster and came from a core document but was not considered because this response was not the top response from this cluster.
    - NOT-CONSIDERED,SUBMITTED,SUBMITTED-A,SUBMITTED-C: The response came from a core document, and was also the top ranked response from the cluster, but the cluster was not high enough in the list to be pooled.
    - INCORRECT,POOLED,SUBMITTED,SUBMITTED-A,SUBMITTED-B,SUBMITTED-C: The response came from a core document, it came from the top K clusters, and was also the top ranked response from that cluster. Therefore, it was pooled, and assessed to be incorrect.
    - CORRECT,POOLED,SUBMITTED,SUBMITTED-A,SUBMITTED-B,SUBMITTED-C: The response came from a core document, it came from the top K clusters, and was also the top ranked response from tha
t cluster. Therefore, it was pooled, and assessed to be correct.
    - CORRECT,POOLED,REDUNDANT,SUBMITTED,SUBMITTED-A,SUBMITTED-B,SUBMITTED-C: The response came from a core document, it came from the top K clusters, and was also the top ranked response from that cluster. Therefore, it was pooled, and assessed to be correct. But it was also redundant in terms of the real world entity it points to as determined during assessment.


Following is the list of categories corresponding to column # 10:

      - RIGHT: Response considered right for scoring (Post-policy). This includes responses that were assessed correct (Pre-policy) and were not redundant (Pre-policy)
      - WRONG: Response considered wrong for scoring (Post-policy). This included responses that were either assessed as incorrect (Pre-policy) or were redundant (Pre-policy)
      - NOT-CONSIDERED: Response that were not considered

## Task2 zerohop scores

### AP_SUBMISSION_LINE

These entries show what ranking was used for computing AP where ties are broken using the following strategies:
  1. BESTCASE (see AP-B above)
  2. WORSECASE (see AP-W above)
  3. TRECEVAL (see AP-T above)

These entries contain 13 values in different columns as shown:

    - Column # 1: DEBUG_INFO
    - Column # 2: AP_SUBMISSION_LINE
    - Column # 3: BESTCASE or WORSTCASE or TRECEVAL
    - Column # 4: Query ID
    - Column # 5: Document ID
    - Column # 6: Mention span
    - Column # 7: Rank
    - Column # 8: Score
    - Column # 9: RunID
    - Column # 10: RIGHT | WRONG
    - Column # 11: Filename and line number where response was found

### ASSESSMENT_INFO

These entries list all the responses read from the validated SPARQL output file along with corresponding confidence aggregation file; and show assessment information corresponding to the response.

These entries contain 9 values in different columns as shown:

    - Column # 1: DEBUG_INFO
    - Column # 2: ASSESSMENT_INFO
    - Column # 3: Query ID
    - Column # 4: KB ID of the entity in query
    - Column # 5: Mention span
    - Column # 6: Cluster ID
    - Column # 7: Aggregated confidence value
    - Column # 8: Pre-policy assessment information and response categorization
    - Column # 9: Post-policy response categorization

Following is the list of categories corresponding to column # 8:

    - CORRECT: Response was assessed to be correct
    - INCORRECT: Response was assessed to be incorrect
    - POOLED: Response was included in the pool
    - REDUNDANT: Response was correct but also redundant because another correct response with the same document was submitted
    - SUBMITTED: One of mention span with the highest JUSTIFICATION_CONFIDENCE mention span from each document from the top cluster. This effectively is the total number of documents in the responses corresponding to the top cluster.
    - SUBMITTED-A: All responses
    - SUBMITTED-B: Response submitted for the best matching cluster

Responses were found to have one of the following group of categories:

    - SUBMITTED-A: The response does not belong to the top cluster
    - SUBMITTED-A,SUBMITTED-B: The response belongs to the top cluster but the response was not the one that corresponds to the highest JUSTIFICATION_CONFIDENCE
    - NOTPOOLED,SUBMITTED,SUBMITTED-A,SUBMITTED-B: The response belongs to the top cluster and also corresponds to the highest JUSTIFICATION_CONFIDENCE but did not have high enough value of aggregate confidence to be pooled
    - INCORRECT,POOLED,SUBMITTED,SUBMITTED-A,SUBMITTED-B: The response belongs to the top cluster and also corresponds to the highest JUSTIFICATION_CONFIDENCE and had high enough aggregate confidence value to be pooled and was assessed to be incorrect
    - CORRECT,POOLED,SUBMITTED,SUBMITTED-A,SUBMITTED-B: The response belongs to the top cluster and also corresponds to the highest JUSTIFICATION_CONFIDENCE and had high enough aggregate confidence value to be pooled and was assessed to be correct

Following is the list of categories corresponding to column # 9:

      - RIGHT: Response considered right for scoring (Post-policy). This includes responses that were assessed correct (Pre-policy) and were not redundant (Pre-policy)
      - WRONG: Response considered wrong for scoring (Post-policy). This included responses that were either assessed as incorrect (Pre-policy) or were redundant (Pre-policy)
      - NOT-CONSIDERED: Response that were not considered

## Task1 graph scores

### Strategy 1

#### ASSESSMENT_INFO

These log entries report assessment and evaluation information corresponding to all the responses read from the output of confidence aggregator.

These entries contain 8 values in different columns as shown:

    - Column # 1: DEBUG_INFO
    - Column # 2: ASSESSMENT_INFO
    - Column # 3: Query ID
    - Column # 4: Document ID
    - Column # 5: Predicate Justification span
    - Column # 6: Object Justification span
    - Column # 7: Pre-policy assessment information and response categorization
    - Column # 8: Post-policy assessment information and response categorization

Following is the list of categories corresponding to column # 7:

    - SUBMITTED
    - POOLED
    - CORRECT
    - INCORRECT
    - PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT
    - REDUNDANT

Following is the list of categories corresponding to column # 8:

    - RIGHT
    - WRONG
    - IGNORE

Combinations of Pre-and-post-policy assessment information and response categorization:
    - PRE_POLICY_ASSESSMENT=CORRECT,POOLED,PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT,REDUNDANT,SUBMITTED POST_POLICY_ASSESSMENT=IGNORE
    - PRE_POLICY_ASSESSMENT=CORRECT,POOLED,PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT,SUBMITTED POST_POLICY_ASSESSMENT=RIGHT
    - PRE_POLICY_ASSESSMENT=CORRECT,POOLED,SUBMITTED POST_POLICY_ASSESSMENT=WRONG
    - PRE_POLICY_ASSESSMENT=INCORRECT,POOLED,SUBMITTED POST_POLICY_ASSESSMENT=WRONG

#### GROUND_TRUTH_INFO RAW

These log entries show ground truth information as read from assessment package.

These entries contain 13 values in different columns as shown below:

      - Column # 1: DEBUG_INFO
      - Column # 2: GROUND_TRUTH_INFO
      - Column # 3: RAW
      - Column # 4: Predicate
      - Column # 5: Document ID
      - Column # 6: Predicate Justification span
      - Column # 7: Object Justification span
      - Column # 8: Correctness of Predicate Justification span
      - Column # 9: Linkability of Predicate Justification span to Object Jusification
      - Column # 10: Object equivalence class as read
      - Column # 11: Object equivalence class used for scoring (as read or generated; generated if the subject was a singleton)
      - Column # 12: Subject equivalence class as read
      - Column # 13: Subject equivalence class used for scoring (as read or generated; generated if the subject was a singleton)

#### GROUND_TRUTH_INFO DETAIL

These entries shows edge equivalence classes found in ground truth.

These entries contain the following nine values in different columns:

      - Column # 1: DEBUG_INFO
      - Column # 2: GROUND_TRUTH_INFO
      - Column # 3: DETAIL
      - Column # 4: Query ID
      - Column # 5: Document ID
      - Column # 6: Edge equivalence class
      - Column # 7: Subject equivalence class
      - Column # 8: Predicate
      - Column # 9: Object equivalence class

## Task2 graph queries

### Strategy 1

#### ASSESSMENT_INFO

These log entries report assessment and evaluation information corresponding to all the responses read from the output of confidence aggregator.

These entries contain the following eight values in different columns:

    - Column # 1: DEBUG_INFO
    - Column # 2: ASSESSMENT_INFO
    - Column # 3: Query ID
    - Column # 4: Document ID
    - Column # 5: Predicate Justification span
    - Column # 6: Object Justification span
    - Column # 7: Pre-policy assessment information and response categorization
    - Column # 8: Post-policy assessment information and response categorization

Pre-policy assessment information and response categorization:
    - SUBMITTED
    - POOLED
    - NOTPOOLED
    - CORRECT
    - INCORRECT
    - PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT
    - OBJECT_LINKABLE_TO_QUERY_ENTITY
    - REDUNDANT

Post-policy assessment information and response categorization:
    - RIGHT
    - WRONG
    - IGNORE
    - NOT-CONSIDERED

Combinations of Pre-and-post-policy assessment information and response categorization:
    - PRE_POLICY_ASSESSMENT=NOTPOOLED,SUBMITTED POST_POLICY_ASSESSMENT=NOT-CONSIDERED
    - PRE_POLICY_ASSESSMENT=CORRECT,POOLED,SUBMITTED POST_POLICY_ASSESSMENT=WRONG
    - PRE_POLICY_ASSESSMENT=INCORRECT,POOLED,SUBMITTED POST_POLICY_ASSESSMENT=WRONG
    - PRE_POLICY_ASSESSMENT=CORRECT,POOLED,PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT,SUBMITTED POST_POLICY_ASSESSMENT=WRONG
    - PRE_POLICY_ASSESSMENT=CORRECT,OBJECT_LINKABLE_TO_QUERY_ENTITY,POOLED,PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT,SUBMITTED POST_POLICY_ASSESSMENT=RIGHT
    - PRE_POLICY_ASSESSMENT=CORRECT,OBJECT_LINKABLE_TO_QUERY_ENTITY,POOLED,PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT,REDUNDANT,SUBMITTED POST_POLICY_ASSESSMENT=IGNORE

#### SALIENT_READ

These log entries report edges read from ground truth as salient to LDC's prevailing theories.

These entries contain the following seven values in different columns:

      - Column # 1: DEBUG_INFO
      - Column # 2: SALIENT_READ
      - Column # 3: LINE or RECORDED (LINE shows as information as read from file; RECORED shows what information was stored after modification)
      - Column # 4: Subject equivalence class
      - Column # 5: Predicate
      - Column # 6: Object equivalence class
      - Column # 7: Source file name and line number

#### SALIENT_FOR_QUERY

These log entries report edges salient for query using the follwing four fields:

      - Column # 1: DEBUG_INFO
      - Column # 2: SALIENT_FOR_QUERY
      - Column # 3: Subject
      - Column # 4: Query ID (this bound the object and role)

#### GROUND_TRUTH_INFO

These log entries show ground truth information as read from assessment package.

These entries contain the following 13 values in different columns:

      - Column # 1: DEBUG_INFO
      - Column # 2: GROUND_TRUTH_INFO
      - Column # 3: RAW
      - Column # 4: Predicate
      - Column # 5: Document ID
      - Column # 6: Predicate Justification span
      - Column # 7: Object Justification span
      - Column # 8: Correctness of Predicate Justification span
      - Column # 9: Linkability of Predicate Justification span to Object Jusification
      - Column # 10: Object equivalence class as read
      - Column # 11: Object equivalence class used for scoring (as read or generated; generated if the subject was a singleton)
      - Column # 12: Subject equivalence class as read
      - Column # 13: Subject equivalence class used for scoring (as read or generated; generated if the subject was a singleton)

### Strategy 2

#### ASSESSMENT_INFO

These log entries report assessment and evaluation information corresponding to all the responses read from the output of confidence aggregator.

Each entry contains 10 values in the following columns:

    - Column # 1: DEBUG_INFO
    - Column # 2: ASSESSMENT_INFO
    - Column # 3: Query ID
    - Column # 4: Document ID
    - Column # 5: Predicate Justification span
    - Column # 6: Object Justification span
    - Column # 7: Subject Cluster ID
    - Column # 8: Object Cluster ID
    - Column # 9: Pre-policy assessment information and response categorization
    - Column # 10: Post-policy assessment information and response categorization

Pre-policy assessment information and response categorization:
    - SUBMITTED
    - POOLED
    - NOTPOOLED
    - CORRECT
    - INCORRECT
    - PREDICATE_JUSTIFICATION_LINKABLE_TO_OBJECT
    - OBJECT_LINKABLE_TO_QUERY_ENTITY

Post-policy assessment information and response categorization:
    - RIGHT
    - WRONG
    - NOT-CONSIDERED

#### FRAME_QUERY

These log entries reports query to frame mappings using the following fields:

    - Column # 1: DEBUG_INFO
    - Column # 2: FRAME_QUERY
    - Column # 3: Frame ID
    - Column # 4: Query ID

#### CORRECT_EDGE

These log entries provide information about correct edges found in responses using the following fields:

    - Column # 1: DEBUG_INFO
    - Column # 2: CORRECT_EDGE
    - Column # 3: Frame ID
    - Column # 4: Query ID
    - Column # 5: Document ID
    - Column # 6: Subject Cluster ID
    - Column # 7: Predicate Justification span
    - Column # 8: Object Justification span
    - Column # 9: Rank
    - Column # 10: Subject equivalence class
    - Column # 11: Predicate
    - Column # 12: Object equivalence class

#### GROUND_TRUTH_INFO

These log entries show ground truth information as read from assessment package using the following columns:

      - Column # 1: DEBUG_INFO
      - Column # 2: GROUND_TRUTH_INFO
      - Column # 3: RAW
      - Column # 4: Predicate
      - Column # 5: Document ID
      - Column # 6: Predicate Justification span
      - Column # 7: Object Justification span
      - Column # 8: Correctness of Predicate Justification span
      - Column # 9: Linkability of Predicate Justification span to Object Jusification
      - Column # 10: Object equivalence class as read
      - Column # 11: Object equivalence class used for scoring (as read or generated; generated if the subject was a singleton)
      - Column # 12: Subject equivalence class as read
      - Column # 13: Subject equivalence class used for scoring (as read or generated; generated if the subject was a singleton)

# Example submission files and scores

In order to demonstrate the usage, the scorer comes with example submission files and corresponding scores.

## Scoring example ZeroHop responses for M9

Example ZeroHop responses can be found at the following directory `examples/M9/zerohop_response`:

	1. TA1 example submission: `examples/M9/zerohop_response/AIDA_TA1_teamA_run_1`
	2. TA2 example submission: `examples/M9/zerohop_response/AIDA_TA2_teamA_run_1`

In order to score these example submissions, you may run the following command:

~~~
cd examples/M9
make
~~~

The score and debug files will be produced in `examples/M9/zerohop_response/output_scores/`.

Note: The scorer does not overwrite score and debug file, and therefore, it is necessary to remove these files if they already exist. Also, note that the input to scorer is a pathfile containing paths of all the input xml response files.

# Revision history
## 10/28/2019
	- First version for M18
## 2/25/2019
	- Minor edits
## 2/24/2019
	- Documentation on how to score example ZeroHop responses added
## 2/23/2019
	- First version
