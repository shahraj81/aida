ROOT=/absolute/path/to/aida/tools/generate-aif
ANNOTATIONS_DIR=/absolute/path/to/annotations
TA1ANNOTATIONS=LDC2021E15_AIDA_Phase_3_TA1_Practice_Topic_Annotation_V3.0
TA2ANNOTATIONS=$(TA1ANNOTATIONS)
TA3ANNOTATIONS=LDC2021E16_AIDA_Phase_3_TA3_Practice_Topic_Annotation_V2.0
HOST_OUTPUT_DIR=$(ROOT)/output/$(ANNOTATIONS)

GRAPHDB_VERSION=9.3.3
GRAPHDB_EDITION=free

all:
	@echo "Usage: make [clean|build|rebuild|task1|task2|task3]"

clean:
	docker system prune -f
	docker builder prune -af
	docker image rm generate-aif

rebuild: clean build

build:
	docker build \
	  --build-arg version=$(GRAPHDB_VERSION) \
	  --build-arg edition=$(GRAPHDB_EDITION) \
	  -t generate-aif .

task1:
	make generate \
	  TASK=task1 \
	  HOST_INPUT_DIR=$(ANNOTATIONS_DIR)/$(TA1ANNOTATIONS)/data \
	  HOST_OUTPUT_DIR=$(OUTPUT_DIR)/$(TA1ANNOTATIONS)

task2:
	make generate \
	  TASK=task2 \
	  HOST_INPUT_DIR=$(ANNOTATIONS_DIR)/$(TA2ANNOTATIONS)/data \
	  HOST_OUTPUT_DIR=$(OUTPUT_DIR)/$(TA2ANNOTATIONS)

task3:
	make generate \
	  TASK=task3 \
	  HOST_INPUT_DIR=$(ANNOTATIONS_DIR)/$(TA3ANNOTATIONS)/data/ta3_ldc \
	  HOST_OUTPUT_DIR=$(OUTPUT_DIR)/$(TA3ANNOTATIONS)

generate:
	docker run \
	  --env TASK=$(TASK) \
	  -v $(HOST_INPUT_DIR):/annotations:ro \
	  -v $(HOST_OUTPUT_DIR)/$(TASK):/output \
	-it generate-aif
