HOST_INPUT_DIR=/Users/skr1/Code/aida/tools/aida-evaluation/M18-data/runs/LDC-TA1-test
HOST_OUTPUT_DIR=/Users/skr1/Code/aida/tools/aida-evaluation/M18-data/example-output/LDC-TA1-test
GRAPHDB_VERSION=9.2.1
GRAPHDB_EDITION=free
HOST_GRAPHDB_PORT=7200
CONTAINER_GRAPHDB_PORT=7200

all:
	@echo "Usage: make [build|run]"	

build:
	docker build \
	       --build-arg version=$(GRAPHDB_VERSION) \
	       --build-arg edition=$(GRAPHDB_EDITION) \
	       -t aida-evaluation .

run:
	docker run \
		-p $(HOST_GRAPHDB_PORT):$(CONTAINER_GRAPHDB_PORT) \
		-v $(HOST_INPUT_DIR):/evaluate:ro \
		-v $(HOST_OUTPUT_DIR):/score \
	-it aida-evaluation
