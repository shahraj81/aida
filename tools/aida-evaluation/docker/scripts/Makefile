all:
	ifeq ($(TASK), "task1")
		@echo "running task1 evaluation pipeline"
		python3 run_task1_evaluation_pipeline.py \
		  --run $(RUNID) \
		  --runtype $(RUNTYPE) \
		  $(ENG_TEXT_IOU_THRESHOLD) \
		  $(SPA_TEXT_IOU_THRESHOLD) \
		  $(RUS_TEXT_IOU_THRESHOLD) \
		  $(IMAGE_IOU_THRESHOLD) \
		  $(VIDEO_IOU_THRESHOLD)
	else
		ifeq (($(TASK), "task2")
			@echo "running task2 evaluation pipeline"
			python3 run_task2_evaluation_pipeline.py \
			  --run $(RUNID) \
			  --runtype $(RUNTYPE) \
			  --aws_access_key_id $(AWS_ACCESS_KEY_ID) \
			  --aws_secret_access_key $(AWS_SECRET_ACCESS_KEY)
		else
			@echo "unexpected value of environment variable TASK"
	endif
