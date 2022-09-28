ROOT=/absolute/path/to/aida/tools/aida-evaluation

RUNTYPE=practice

RUNS=$(ROOT)/M54-$(RUNTYPE)/runs
SCORES=$(ROOT)/M54-$(RUNTYPE)/scores
RUNID=example-run
HOST_INPUT_DIR=$(RUNS)/$(RUNID)
HOST_OUTPUT_DIR=$(SCORES)/$(RUNID)
HOST_DATA_DIR=$(ROOT)/docker/AUX-data/M54-$(RUNTYPE)/
GRAPHDB_VERSION=10.0.2

ENG_TEXT_IOU_THRESHOLD=0.1
SPA_TEXT_IOU_THRESHOLD=0.1
RUS_TEXT_IOU_THRESHOLD=0.1
IMAGE_IOU_THRESHOLD=0.1
VIDEO_IOU_THRESHOLD=0.1

USERID=$$(id -u)
GROUPID=$$(id -g)

all:
	@echo "Usage: make [build|task1-example|task2-example|task3-example|task1|task2|task3]"

clean:
	docker system prune -f
	docker image rm aida-evaluation

build:
	docker build \
	       --build-arg userid=$(USERID) \
	       --build-arg groupid=$(GROUPID) \
	       --build-arg version=$(GRAPHDB_VERSION) \
	       -t aida-evaluation .

rebuild: clean build

task1-example:
	make task1 \
	  RUNID=example-task1-run \
	  HOST_INPUT_DIR=$(ROOT)/M54-practice/runs/example-task1-run \
	  HOST_OUTPUT_DIR=$(ROOT)/M54-practice/scores/example-task1-run

task2-example:
	make task2 \
	  RUNID=example-task2-run \
	  HOST_INPUT_DIR=$(ROOT)/M54-practice/runs/example-task2-run \
	  HOST_OUTPUT_DIR=$(ROOT)/M54-practice/scores/example-task2-run

task3-example:
	make task3 \
	  RUNID=example-task3-run \
	  HOST_INPUT_DIR=$(ROOT)/M54-practice/runs/example-task3-run \
	  HOST_OUTPUT_DIR=$(ROOT)/M54-practice/scores/example-task3-run

task3-example-aws-1:
	make task3 \
	  RUNID=example-task3-run-aws-1 \
	  HOST_INPUT_DIR=$(ROOT)/M54-practice/runs/example-task3-run-aws-1 \
	  HOST_OUTPUT_DIR=$(ROOT)/M54-practice/scores/example-task3-run-aws-1

task3-example-aws-2:
	make task3 \
	  RUNID=example-task3-run-aws-2 \
	  HOST_INPUT_DIR=$(ROOT)/M54-practice/runs/example-task3-run-aws-2 \
	  HOST_OUTPUT_DIR=$(ROOT)/M54-practice/scores/example-task3-run-aws-2

task1:
	mkdir $(HOST_OUTPUT_DIR)
	docker run \
	  --env RUNID=$(RUNID) \
	  --env RUNTYPE=$(RUNTYPE) \
	  --env TASK=task1 \
	  --env ENG_TEXT_IOU_THRESHOLD=$(ENG_TEXT_IOU_THRESHOLD) \
	  --env SPA_TEXT_IOU_THRESHOLD=$(SPA_TEXT_IOU_THRESHOLD) \
	  --env RUS_TEXT_IOU_THRESHOLD=$(RUS_TEXT_IOU_THRESHOLD) \
	  --env IMAGE_IOU_THRESHOLD=$(IMAGE_IOU_THRESHOLD) \
	  --env VIDEO_IOU_THRESHOLD=$(VIDEO_IOU_THRESHOLD) \
	  -v $(HOST_INPUT_DIR):/evaluate:ro \
	  -v $(HOST_OUTPUT_DIR):/score \
	  -v $(HOST_DATA_DIR):/data \
	  -u $(USERID):$(GROUPID) \
	-it aida-evaluation

task2:
	docker run \
	  --env RUNID=$(RUNID) \
	  --env RUNTYPE=$(RUNTYPE) \
	  --env TASK=task2 \
	  --env AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) \
	  --env AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY) \
	  -v $(HOST_INPUT_DIR):/evaluate:ro \
	  -v $(HOST_OUTPUT_DIR):/output \
	  -v $(HOST_DATA_DIR):/data \
	-it aida-evaluation

task3:
	docker run \
	  --env RUNID=$(RUNID) \
	  --env RUNTYPE=$(RUNTYPE) \
	  --env TASK=task3 \
	  --env DEPTH=$(DEPTH) \
	  --env AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) \
	  --env AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY) \
	  -v $(HOST_INPUT_DIR):/evaluate:ro \
	  -v $(HOST_OUTPUT_DIR):/output \
	  -v $(HOST_DATA_DIR):/data \
	-it aida-evaluation
