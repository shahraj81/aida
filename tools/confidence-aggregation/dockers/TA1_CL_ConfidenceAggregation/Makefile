HOST_INPUT_DIR=/absolute/path/to/inputdir
HOST_OUTPUT_DIR=/absolute/path/to/outputdir

all:
	@echo "Usage: make [build|clean|kill-all|prune|rebuild|run]"

kill-all:
	docker kill $(docker ps -q)
	docker container stop $(docker container ls -aq)
	docker container rm $(docker container ls -aq)
	docker rmi $(docker images -q)

prune:
	docker system prune -af

clean:
	docker image rm default-ta1-class-confidence-aggregation --force

rebuild: clean prune build

build:
	docker build \
	       -t  default-ta1-class-confidence-aggregation .

run:
	docker run \
	  -v $(HOST_INPUT_DIR):/mnt/input \
	  -v $(HOST_OUTPUT_DIR):/mnt/output \
	  -it default-ta1-class-confidence-aggregation
