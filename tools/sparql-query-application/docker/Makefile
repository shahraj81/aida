ROOT=/absolute/path/to/aida/tools/sparql-query-application
M18DATA=M18-data
TASK=task1
TYPE=class
RUN=task1-team-X-run-A

HOST_RUN_DIR=$(ROOT)/$(M18DATA)/runs/task1-team-X-run-A
HOST_QUERIES_DIR=$(ROOT)/$(M18DATA)/queries/task1_class_queries
HOST_OUTPUT_DIR=$(ROOT)/$(M18DATA)/output/task1-team-X-run-A

GRAPHDB_VERSION=8.11.0
GRAPHDB_EDITION=free
HOST_GRAPHDB_PORT=8200
CONTAINER_GRAPHDB_PORT=7200

all:
	@echo "Usage: make [build|clean|prune|rebuild|run]"

prune:
	docker system prune -a -f

clean:
	docker image rm resolve-queries --force

build:
	docker build \
	       --build-arg version=$(GRAPHDB_VERSION) \
	       --build-arg edition=$(GRAPHDB_EDITION) \
	       -t resolve-queries .

rebuild: clean build

# Apply sparql queries to all KBs in the runs directory
run:
	@echo "--creating output directory: $(HOST_OUTPUT_DIR)"
	mkdir -p $(HOST_OUTPUT_DIR)
	@echo "--running docker begins"
	docker run -v $(HOST_OUTPUT_DIR):/mnt/output \
             -v $(HOST_RUN_DIR):/mnt/run \
             -v $(HOST_QUERIES_DIR):/mnt/queries \
	     -p $(HOST_GRAPHDB_PORT):$(CONTAINER_GRAPHDB_PORT) \
	     -it resolve-queries
	@echo "--running docker ends"

run-all: run-task1 run-task2 run-task3

run-task1:
	##############################
	# RUN_ID = task1-team-X-run-A
	##############################
	# QUERY_TYPE = task1_class_queries
	make run \
	 HOST_RUN_DIR=$(ROOT)/$(M18DATA)/runs/task1-team-X-run-A \
	 HOST_QUERIES_DIR=$(ROOT)/$(M18DATA)/queries/task1_class_queries \
	 HOST_OUTPUT_DIR=$(ROOT)/$(M18DATA)/output/task1-team-X-run-A

	# QUERY_TYPE = task1_graph_queries
	make run \
	 HOST_RUN_DIR=$(ROOT)/$(M18DATA)/runs/task1-team-X-run-A \
	 HOST_QUERIES_DIR=$(ROOT)/$(M18DATA)/queries/task1_graph_queries \
	 HOST_OUTPUT_DIR=$(ROOT)/$(M18DATA)/output/task1-team-X-run-A

run-task2:
	##############################
	# RUN_ID = task2-team-X-run-D
	##############################
	# QUERY_TYPE = task2_zerohop_queries
	make run \
	 HOST_RUN_DIR=$(ROOT)/$(M18DATA)/runs/task2-team-X-run-D \
	 HOST_QUERIES_DIR=$(ROOT)/$(M18DATA)/queries/task2_zerohop_queries \
	 HOST_OUTPUT_DIR=$(ROOT)/$(M18DATA)/output/task2-team-X-run-D

 	# QUERY_TYPE = task2_graph_queries
	make run \
	 HOST_RUN_DIR=$(ROOT)/$(M18DATA)/runs/task2-team-X-run-D \
	 HOST_QUERIES_DIR=$(ROOT)/$(M18DATA)/queries/task2_graph_queries \
	 HOST_OUTPUT_DIR=$(ROOT)/$(M18DATA)/output/task2-team-X-run-D

run-task3:
	##############################
        # RUN_ID = task3-team-X-run-B
        ##############################
        # QUERY_TYPE = task3_graph_queries
	make run \
	 HOST_RUN_DIR=$(ROOT)/$(M18DATA)/runs/task3-team-X-run-B \
	 HOST_QUERIES_DIR=$(ROOT)/$(M18DATA)/queries/task3_graph_queries \
	 HOST_OUTPUT_DIR=$(ROOT)/$(M18DATA)/output/task3-team-X-run-B
