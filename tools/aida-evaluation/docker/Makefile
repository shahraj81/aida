ROOT=/absolute/path/to/aida/tools/aida-evaluation

RUNTYPE=practice

RUNS=$(ROOT)/M54-$(RUNTYPE)/runs
SCORES=$(ROOT)/M54-$(RUNTYPE)/scores
RUNID=example-run
HOST_INPUT_DIR=$(RUNS)/$(RUNID)
HOST_OUTPUT_DIR=$(SCORES)/$(RUNID)
HOST_DATA_DIR=$(ROOT)/docker/AUX-data/M54-$(RUNTYPE)/
GRAPHDB_VERSION=10.0.2

USERID=$$(id -u)
GROUPID=$$(id -g)

ALPHA=0.9
CACHE='/data/AUX-data/cache.txt'
IOU_THRESHOLDS='eng:image:0.1,eng:text:0.1,eng:video:0.1,rus:image:0.1,rus:text:0.1,rus:video:0.1,spa:image:0.1,spa:text:0.1,spa:video:0.1,ukr:image:0.1,ukr:text:0.1,ukr:video:0.1'
KGTK_API=https://kgtk.isi.edu/similarity_api
LOCK='/data/AUX-data/kgtk.lock'
NN_SIMILARITY_VALUE=0.9
SIMILARITY_TYPES='class,jc'
WAIT=10

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

score-all-task1-runs:
	make score-a-task1-run RUNTYPE=practice RUNID=example-task1-run

score-a-task1-run:
	make task1 \
	  RUNID=$(RUNID) \
	  HOST_INPUT_DIR=$(ROOT)/M54-$(RUNTYPE)/runs/$(RUNID) \
	  HOST_OUTPUT_DIR=$(ROOT)/M54-$(RUNTYPE)/scores/$(RUNID)

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
	  --env ALPHA=$(ALPHA) \
	  --env CACHE=$(CACHE) \
	  --env IOU_THRESHOLDS=$(IOU_THRESHOLDS) \
	  --env KGTK_API=$(KGTK_API) \
	  --env LOCK=$(LOCK) \
	  --env NN_SIMILARITY_VALUE=$(NN_SIMILARITY_VALUE) \
	  --env SIMILARITY_TYPES=$(SIMILARITY_TYPES) \
	  --env WAIT=$(WAIT) \
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
