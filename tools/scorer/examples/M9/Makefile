all: score-example-ta1 score-example-ta2

score-example-ta1:
	cd ../../ && perl AIDA-Score-MASTER.pl \
		-error_file examples/M9/zerohop_response/output_scores/AIDA_TA1_teamA_run_1.log \
		-runid AIDA_TA1_teamA_run_1 \
		examples/M9/zerohop_response/example_coredocs.txt \
		examples/M9/zerohop_response/example_parent_children.tsv \
		examples/M9/zerohop_response/queries_dtd/zerohop_query.dtd \
		examples/M9/zerohop_response/example_queries_xml/zerohop_queries.xml \
		examples/M9/zerohop_response/example_queries_xml/ldc_queries_xml/zerohop_queries.xml \
		examples/M9/zerohop_response/responses_dtd/zerohop_response.dtd \
		examples/M9/zerohop_response/AIDA_TA1_teamA_run_1.pathfile \
		examples/M9/zerohop_response/example_qrels/M09-ZeroHop-FQEC-QREL.tab \
		examples/M9/zerohop_response/output_scores/AIDA_TA1_teamA_run_1.score
		
score-example-ta2:
	cd ../../ && perl AIDA-Score-MASTER.pl \
		-error_file examples/M9/zerohop_response/output_scores/AIDA_TA2_teamA_run_1.log \
		-runid AIDA_TA2_teamA_run_1 \
		examples/M9/zerohop_response/example_coredocs.txt \
		examples/M9/zerohop_response/example_parent_children.tsv \
		examples/M9/zerohop_response/queries_dtd/zerohop_query.dtd \
		examples/M9/zerohop_response/example_queries_xml/zerohop_queries.xml \
		examples/M9/zerohop_response/example_queries_xml/ldc_queries_xml/zerohop_queries.xml \
		examples/M9/zerohop_response/responses_dtd/zerohop_response.dtd \
		examples/M9/zerohop_response/AIDA_TA2_teamA_run_1.pathfile \
		examples/M9/zerohop_response/example_qrels/M09-ZeroHop-FQEC-QREL.tab \
		examples/M9/zerohop_response/output_scores/AIDA_TA2_teamA_run_1.score
		
