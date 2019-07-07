FROM ubuntu:18.04
MAINTAINER shahzad.rajput@nist.gov

# Install system packages
RUN apt-get update && apt-get install -y \
    curl \
    git \
    make \
    unzip

#-------------------------------------------------------------
#  Install Java OpenJDK 8
#-------------------------------------------------------------
RUN \
  apt-get install -y --fix-missing openjdk-8-jdk

# Define JAVA_HOME variable
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64

#-------------------------------------------------------------
# Add user
#-------------------------------------------------------------
ARG userid
RUN addgroup --gid ${userid} ubuntu
RUN useradd -rm -d /home/ubuntu -s /bin/bash -g ${userid} -u ${userid} ubuntu
USER ubuntu
WORKDIR /home/ubuntu

#-------------------------------------------------------------
# Copy required scripts
#-------------------------------------------------------------
COPY --chown=ubuntu:ubuntu ./scripts /scripts

#-------------------------------------------------------------
#  Install GraphDB
#  Taken from the Dockerfile for GraphDB docker available at:
#  https://github.com/Ontotext-AD/graphdb-docker
#-------------------------------------------------------------
# Define arguments need for installation of GraphDB

ARG version=8.10.1
ARG edition=free

ENV GRAPHDB_PARENT_DIR=/scripts/graphdb
ENV GRAPHDB_HOME=${GRAPHDB_PARENT_DIR}/home

ENV GRAPHDB_INSTALL_DIR=${GRAPHDB_PARENT_DIR}/dist

COPY --chown=ubuntu:ubuntu ./AUX-data/graphdb-${edition}-${version}-dist.zip /tmp/

WORKDIR /tmp

RUN mkdir -p ${GRAPHDB_PARENT_DIR} && \
    cd ${GRAPHDB_PARENT_DIR} && \
    unzip /tmp/graphdb-${edition}-${version}-dist.zip && \
    rm /tmp/graphdb-${edition}-${version}-dist.zip && \
    mv graphdb-${edition}-${version} dist && \
    mkdir -p ${GRAPHDB_HOME}

ENV PATH=${GRAPHDB_INSTALL_DIR}/bin:$PATH

#-------------------------------------------------------------
#  Setup entrypoint
#-------------------------------------------------------------

ENTRYPOINT ["make", "-f" , "/scripts/Makefile"]

#-------------------------------------------------------------
# Install SPARQL Evaluation Tool
#-------------------------------------------------------------

# Create directory structure
ENV SPARQL_EVAL_HOME=/scripts/sparql-evaluation
ENV SPARQL_EVAL_CONFIG=${SPARQL_EVAL_HOME}/config
RUN mkdir -p $SPARQL_EVAL_CONFIG

# Copy shadow jar and example configuration to sparql-evaluation directory
COPY --chown=ubuntu:ubuntu ./AUX-data/sparql-evaluation-*-all.jar $SPARQL_EVAL_HOME/
COPY --chown=ubuntu:ubuntu ./AUX-data/Local-config.* $SPARQL_EVAL_CONFIG/

# Copy the custom function jar files to inside GraphDB lib
COPY --chown=ubuntu:ubuntu ./AUX-data/rdf4j-function-* ${GRAPHDB_INSTALL_DIR}/lib/
