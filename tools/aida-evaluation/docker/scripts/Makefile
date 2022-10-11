ifneq ($(AWS_ACCESS_KEY_ID),)
	AWS_ACCESS_KEY_ID_ARG=--aws_access_key_id $(AWS_ACCESS_KEY_ID)
endif

ifneq ($(AWS_SECRET_ACCESS_KEY),)
	AWS_SECRET_ACCESS_KEY_ARG=--aws_secret_access_key $(AWS_SECRET_ACCESS_KEY)
endif

ifneq ($(DEPTH),)
	DEPTH_ARG=--depth $(DEPTH)
endif

all:

ifeq ($(TASK), task1)
	python3.9 run_task1_evaluation_pipeline.py \
	  --run $(RUNID) \
	  --runtype $(RUNTYPE) \
	  --alpha $(ALPHA) \
	  --cache $(CACHE) \
	  --iou_thresholds $(IOU_THRESHOLDS) \
	  --kgtk_api $(KGTK_API) \
	  --lock $(LOCK) \
	  --near_neighbor_similarity_value $(NN_SIMILARITY_VALUE) \
	  --similarity_types $(SIMILARITY_TYPES) \
	  --wait $(WAIT)
else ifeq ($(TASK), task2)
	python3.9 run_task2_evaluation_pipeline.py \
	  --run $(RUNID) --runtype $(RUNTYPE) $(AWS_ACCESS_KEY_ID_ARG) $(AWS_SECRET_ACCESS_KEY_ARG)
else ifeq ($(TASK), task3)
	python3.9 run_task3_evaluation_pipeline.py \
	  --run $(RUNID) --runtype $(RUNTYPE) $(DEPTH_ARG) $(AWS_ACCESS_KEY_ID_ARG) $(AWS_SECRET_ACCESS_KEY_ARG)
else
	@echo "unexpected value of environment variable TASK"
endif
