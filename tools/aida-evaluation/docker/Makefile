ROOT=/absolute/path/to/aida/tools/aida-evaluation
RUNS=$(ROOT)/M36-practice/runs
SCORES=$(ROOT)/M36-practice/scores
RUNID=example-run
HOST_INPUT_DIR=$(RUNS)/$(RUNID)
HOST_OUTPUT_DIR=$(SCORES)/$(RUNID)
GRAPHDB_VERSION=9.3.3
GRAPHDB_EDITION=free

all:
	@echo "Usage: make [build|run]"	

build:
	docker build \
	       --build-arg version=$(GRAPHDB_VERSION) \
	       --build-arg edition=$(GRAPHDB_EDITION) \
	       -t aida-evaluation .

run:
	docker run \
		--env RUNID=$(RUNID) \
		-v $(HOST_INPUT_DIR):/evaluate:ro \
		-v $(HOST_OUTPUT_DIR):/score \
	-it aida-evaluation
