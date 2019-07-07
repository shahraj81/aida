GRAPHDB_BIN=/scripts/graphdb/dist/bin/
LOADRDF=$(GRAPHDB_BIN)/loadrdf
VERDI_SPARQL_EVAL_HOME=/scripts/sparql-evaluation/
VERDI_SPARQL_EVAL_JAR=$(VERDI_SPARQL_EVAL_HOME)/sparql-evaluation-1.0.0-SNAPSHOT-all.jar
REPOSITORY_CONFIG=$(VERDI_SPARQL_EVAL_HOME)/config/Local-config.properties
RUN=/mnt/run
QUERIES=/mnt/queries
OUTPUT=/mnt/output
INTERMEDIATE=$(OUTPUT)/intermediate

all:
	@for KB_FILENAME in $(shell ls ${RUN}); do \
		KB_OUTPUT=$${KB_FILENAME}; \
		cd /scripts && make run-sparql-over-a-kb KB=$${KB_OUTPUT}; \
	done

run-sparql-over-a-kb:
	@echo "--processing KB=$(KB) begins"
	mkdir -p $(OUTPUT)/$(KB)
	$(LOADRDF) -c $(VERDI_SPARQL_EVAL_HOME)/config/Local-config.ttl -f -m parallel $(RUN)/$(KB)
	@echo "--starting GraphDB"
	$(GRAPHDB_BIN)/graphdb -d
	mkdir $(INTERMEDIATE)
	@echo "--waiting for GraphDB"
	sleep 5
	@echo "--applying queries"
	java -jar $(VERDI_SPARQL_EVAL_JAR) \
	                -c $(REPOSITORY_CONFIG) \
	                -q $(QUERIES)/ \
	                -o $(INTERMEDIATE)/
	@echo "--moving output files"
	mv $(INTERMEDIATE)/*/* $(OUTPUT)/$(KB)/
	@echo "--removing directory: $(INTERMEDIATE)"
	rm -rf $(INTERMEDIATE)
	@echo "--stopping GraphDB"
	pkill -9 -f graphdb
	@echo "--processing KB=$(KB) ends"
