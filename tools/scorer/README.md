# Introduction

February 24, 2019

This document describes:

	1. Usage of the Scorer,
	2. How to generate the official scores for ZeroHop responses, 
	3. How to interpret scores output,
	4. How to read the debug file,
	5. Example submission and corresponding scores, and
	6. Revision history

# Usage of the Scorer

~~~
AIDA-Score-MASTER.pl:  Score XML response files

Usage: AIDA-Score-MASTER.pl {-switch {-switch ...}} coredocs docid_mappings queries_dtd queries_xml ldc_queries responses_dtd responses_xml qrel output

Legal switches are:
  -error_file <value>  Specify a file to which error output should be redirected
                         (Default = STDERR).
  -help                Show help
  -queries <value>     File containing query IDs to be scored
  -runid <value>       Run ID of the system being scored (Default = system).
  -version             Print version number and exit
parameters are:
  coredocs        List of core documents to be included in the pool (Required).
  docid_mappings  DocumentID to DocumentElementID mappings (Required).
  queries_dtd     DTD file corresponding to the XML file containing queries
                    (Required).
  queries_xml     The official XML file containing queries (Required).
  ldc_queries     XML file containing queries having LDC nodeids (Required).
  responses_dtd   DTD file corresponding to the XML file containing response
                    (Required).
  responses_xml   File containing path to all the XML response files belonging
                    to a run/submission to be scored (Required).
  qrel            QREL file (Required).
  output          Output file (Required).
~~~

# Generating the official scores for ZeroHop responses

In order to obtain offical scores for a zerohop response file, you may run the following command:

~~~
perl AIDA-Score-MASTER.pl -error_file AIDArun_score.log -runid AIDArun LDC2018E62.P103.coredocs.tsv LDC2018E62.parent_children.tsv queries_dtd/zerohop_query.dtd queries_xml/participants/zerohop_queries.xml queries_xml/ldc/zerohop_queries.xml responses_dtd/zerohop_response.dtd AIDArun qrels/M09_zerohop_core79_qre.txt AIDArun_score.txt 
~~~

# Understanding the output

The current version of the scorer produces micro-average Precision, Recall and F1. 

Micro-averages are computed as:

~~~
Total_Precision = Total_Right / (Total_Right + Total_Wrong)
Total_Recall = Total_Right / Total_GT
Total_F1 = 2 * Total_Precision * Total_Recall / (Total_Precision + Total_Recall)
~~~

## Output fields

For each query, the scorer output the following counts:

~~~
Node      KB id of the node corresponding to the query entrypoint as assigned by LDC,
Mode      Modality of the query entrypoint document element  
RunID     System name
GT        Ground truth
Sub       Number of responses submitted
NtAssd    Number of responses not in the pool of assessed responses
Correct   Number of responses assessed to be correct (Pre-policy)
Dup       Number of responses that were assessed as Correct but found to be duplicate of another Correct in the same submission (Pre-policy)
Incrct    Number of responses assessed to be incorrect (Pre-policy)
Cntd      Number of responses counted for the purpose of computing F1 (Post-policy)
Right     Number of responses counted as Right for the purpose of computing F1 (Post-policy)
Wrong     Number of responses counted as Wrong for the purpose of computing F1 (Post-policy)
Ignrd     Number of responses ignored (Post-policy)
Prec      Computed as: Right / (Right + Wrong)
Recall    Computed as: Right / GT
F1        Computed as: 2 * Precision * Recall / (Precision + Recall)
~~~

Note that we used the following policy decision:

	1. Ignrd = NtAssd + Dup
	2. Right = Correct - Dup
	3. Wrong = Incrct
	4. Cntd  = Sub - Ignrd = Right + Wrong

# Understanding the debug/log file

In this section, we highlight two types of entries in the log file:

	1. GROUND_TRUTH_INFO
	2. ASSESSMENT_INFO

## GROUND_TRUTH_INFO

The scorer reads the QREL and coredocs, and uses the GROUND_TRUTH_INFO tag to log what mention spans are in the pool and what is their respective assessment. An example is given below:

~~~
DEBUG_INFO: GROUND_TRUTH_INFO: NODEID=E0632 MENTION=HC000T65W:(10120,0)-(10133,0) FQEC=HC000T65W:90 CORRECT
      (examples/M9/zerohop_response/example_qrels/M09-ZeroHop-FQEC-QREL.tab line 16)
~~~

This line provides the information that the mention span `HC000T65W:(10120,0)-(10133,0)` is a CORRECT mention of the entity corresponding to the node `E0632` and that this mention falls in the equivalence class (i.e. FQEC) `HC000T65W:90`. Note that for text document elements, FQEC is the document element ID plus the sentence number in which the span falls, whereas video/image bounding boxes, the FQEC is the name of the document element.

The number of distinct FQECs for a given node is value of GT used for computing F1.

## ASSESSMENT_INFO

The scorer reads the responses and uses ASSESSMENT_INFO tag to log what were the pre-policy and post-policy assessments for a response. An example is given below:

~~~
DEBUG_INFO: ASSESSMENT_INFO: NODEID=E0632 QUERYID=AIDA_ZH_2018_37 MENTION=HC000T65W:(10052,0)-(10059,0) PRE_POLICY_ASSESSMENT=NOT_IN_POOL,SUBMITTED POST_POLICY_ASSESSMENT=IGNORED FQEC=UNASSESSED
 (examples/M9/zerohop_response/AIDA_TA1_teamA_run_1/IC00162QM.zerohop_responses.xml line 11)
~~~

# Example submission files and scores

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

Note: The scorer does not overwrite score and debug file, and therefore, it is necessary to remove these files if they already exist.

# Revision history
## 2/24/2019
	- Documentation on how to score example ZeroHop responses added
## 2/23/2019
	- First version
