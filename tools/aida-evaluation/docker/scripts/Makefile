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
	  --kgtk_api $(KGTK_API) \
	  $(ENG_TEXT_IOU_THRESHOLD) \
	  $(SPA_TEXT_IOU_THRESHOLD) \
	  $(RUS_TEXT_IOU_THRESHOLD) \
	  $(IMAGE_IOU_THRESHOLD) \
	  $(VIDEO_IOU_THRESHOLD)
else ifeq ($(TASK), task2)
	python3.9 run_task2_evaluation_pipeline.py \
	  --run $(RUNID) --runtype $(RUNTYPE) $(AWS_ACCESS_KEY_ID_ARG) $(AWS_SECRET_ACCESS_KEY_ARG)
else ifeq ($(TASK), task3)
	python3.9 run_task3_evaluation_pipeline.py \
	  --run $(RUNID) --runtype $(RUNTYPE) $(DEPTH_ARG) $(AWS_ACCESS_KEY_ID_ARG) $(AWS_SECRET_ACCESS_KEY_ARG)
else
	@echo "unexpected value of environment variable TASK"
endif
