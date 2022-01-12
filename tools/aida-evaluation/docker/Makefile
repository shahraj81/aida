ROOT=/absolute/path/to/aida/tools/aida-evaluation

RUNTYPE=develop

RUNS=$(ROOT)/M54-$(RUNTYPE)/runs
SCORES=$(ROOT)/M54-$(RUNTYPE)/scores
RUNID=example-run
HOST_INPUT_DIR=$(RUNS)/$(RUNID)
HOST_OUTPUT_DIR=$(SCORES)/$(RUNID)
HOST_DATA_DIR=$(ROOT)/docker/AUX-data/M54-$(RUNTYPE)/
GRAPHDB_VERSION=9.10.3
GRAPHDB_EDITION=free

all:
	@echo "Usage: make [build|task3-example|task3]"

build:
	docker build \
	       --build-arg version=$(GRAPHDB_VERSION) \
	       --build-arg edition=$(GRAPHDB_EDITION) \
	       -t aida-evaluation .

task3-example:
	make task3 \
	  RUNID=example-task3-run \
	  HOST_INPUT_DIR=$(ROOT)/M54-$(RUNTYPE)/runs/example-task3-run \
	  HOST_OUTPUT_DIR=$(ROOT)/M54-$(RUNTYPE)/scores/example-task3-run

task3:
	docker run \
	  --env RUNID=$(RUNID) \
	  --env RUNTYPE=$(RUNTYPE) \
	  --env TASK=task3 \
	  --env AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) \
	  --env AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY) \
	  -v $(HOST_INPUT_DIR):/evaluate:ro \
	  -v $(HOST_OUTPUT_DIR):/output \
	  -v $(HOST_DATA_DIR):/data \
	-it aida-evaluation
