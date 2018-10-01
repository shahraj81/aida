SPARQL=/home/skr1/local_installations/SPARQL/apache-jena-3.6.0/bin/sparql

all: example-class example-zerohop example-graph

clean:
	rm -rf example/intermediate/class_queries_data example/output/class_queries_output
	rm -rf example/intermediate/zerohop_queries_data example/output/zerohop_queries_output
	rm -rf example/intermediate/graph_queries_data example/output/graph_queries_output

example-class:
	perl AIDA-ResolveQueries-MASTER.pl -error_file rq_example_class.errlog -sparql $(SPARQL) example/input/example_parent_children.tsv example/input/example_queries_dtd/class_query.dtd example/input/example_queries_xml/example_class_queries.xml example/input/example_submission/example_ta1_system_run_1 example/intermediate/class_queries_data example/output/class_queries_output

example-zerohop:
	perl AIDA-ResolveQueries-MASTER.pl -error_file rq_example_zerohop.errlog -sparql $(SPARQL) example/input/example_parent_children.tsv example/input/example_queries_dtd/zerohop_query.dtd example/input/example_queries_xml/example_zerohop_queries.xml example/input/example_submission/example_ta1_system_run_1 example/intermediate/zerohop_queries_data example/output/zerohop_queries_output

example-graph:
	perl AIDA-ResolveQueries-MASTER.pl -error_file rq_example_graph.errlog -sparql $(SPARQL)  example/input/example_parent_children.tsv example/input/example_queries_dtd/graph_query.dtd example/input/example_queries_xml/example_graph_queries.xml example/input/example_submission/example_ta1_system_run_1 example/intermediate/graph_queries_data example/output/graph_queries_output
