# How to generate AIF

In order to generate AIF follow the steps given below:

	1. Build the generate-aif docker image,
	2. Modify paths in Makefile to reflect your system specific locations
	3. Run the docker, and
	4. Examine the log files for problems

# Introduction

This document describes how to run the AIDA Task1/Task2/Task3 AIF generation pipeline.

# How to build the docker image?

The docker has been tested with `graphdb-free-9.3.3-dist` but this section also describes how to configure it to work with a different version.

Independent of which version of GraphDB you are using, you would need to first update the value of the variable named `ROOT` on the first line of `./docker/Makefile` (as shown below) to reflect your system specific location of the directory where the code form the [AIDA evaluation repository](https://github.com/shahraj81/aida) is placed:

~~~
ROOT=/absolute/path/to/aida/tools/generate-aif
~~~

Additionally, you must also update the value of the variable named `ANNOTATIONS_DIR` on the second line of `./docker/Makefile` (as shown below) to reflect your system specific location of the directory where the annotations (from LDC) have been placed:

~~~
ANNOTATIONS_DIR=/absolute/path/to/annotations 
~~~

## Using the tested version of GraphDB

In order to build the docker image with the tested version of GraphDB you would need to:

1. Download `graphdb-free-9.3.3-dist.zip` from `https://www.ontotext.com/free-graphdb-download/`, and place it inside `./docker/`, and

2. Run the following command:

  ~~~
  cd docker
  make build
  ~~~

## Using another version of GraphDB

In order to build the docker image with a different version of GraphDB you would need to:

1. Download the installer of the GraphDB version that you would like to use (the name of which must be of the form`graphdb-[otheredition]-[otherversion]-dist.zip`), and place it inside `./docker/`, and

2. Run the following command:

~~~
cd docker
make build GRAPHDB_EDITION=otheredition GRAPHDB_VERSION=otherversion
~~~

# How to apply the docker?

Once the variables mentioned above have been modified, you may run the following task-specific commands to generate AIF.

## Task1

~~~
cd docker
make task1
~~~

## Task2

~~~
cd docker
make task2
~~~

## Task3

~~~
cd docker
make task3
~~~

# Examine the log files for problems

Finally, examine the log files for problems.
