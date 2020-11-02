FROM ubuntu:18.04
MAINTAINER shahzad.rajput@nist.gov

# Set timezone
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime

# Install system packages
RUN apt-get update && apt update && apt-get install -y \
    curl \
    git \
    make \
    python3 \
    python3-pip \
    unzip \
    perlbrew \
    tzdata \
    vim

#-------------------------------------------------------------
# Install munkres
#-------------------------------------------------------------

RUN pip3 install munkres

#-------------------------------------------------------------
#  Install awscli
#-------------------------------------------------------------

RUN pip3 --no-cache-dir install --upgrade awscli

#-------------------------------------------------------------
#  Install Java OpenJDK 8
#-------------------------------------------------------------
RUN \
  apt-get install -y --fix-missing openjdk-8-jdk

# Define JAVA_HOME variable
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64

# Reconfigure tzdata
RUN dpkg-reconfigure -f noninteractive tzdata

#-------------------------------------------------------------
#  Install GraphDB
#  Taken from the Dockerfile for GraphDB docker available at:
#  https://github.com/Ontotext-AD/graphdb-docker
#-------------------------------------------------------------
# Define arguments need for installation of GraphDB

ARG version=9.3.3
ARG edition=free

ENV GRAPHDB_PARENT_DIR=/opt/graphdb
ENV GRAPHDB_HOME=${GRAPHDB_PARENT_DIR}/home
ENV GRAPHDB_INSTALL_DIR=${GRAPHDB_PARENT_DIR}/dist
ENV SPARQL_EVAL_HOME=/opt/sparql-evaluation
ENV PATH=${GRAPHDB_INSTALL_DIR}/bin:$PATH

RUN mkdir scripts

COPY ./graphdb-${edition}-${version}-dist.zip /tmp/

WORKDIR /tmp

RUN mkdir -p ${GRAPHDB_PARENT_DIR} && \
    cd ${GRAPHDB_PARENT_DIR} && \
    unzip -q /tmp/graphdb-${edition}-${version}-dist.zip && \
    rm /tmp/graphdb-${edition}-${version}-dist.zip && \
    mv graphdb-${edition}-${version} dist && \
    mkdir -p ${GRAPHDB_HOME}

RUN mkdir $SPARQL_EVAL_HOME

# Install JSON

ENV PERLBREW_PATH=/root/perl5/perlbrew/bin
RUN perlbrew install-cpanm
RUN $PERLBREW_PATH/cpanm install JSON

# Setup the AIDA repository
WORKDIR /scripts

RUN git clone https://github.com/shahraj81/aida.git

WORKDIR /scripts/aida

RUN git checkout AIDAED-v2020.2.0

RUN cp /scripts/aida/python/input/aux_data/log_specifications.txt /scripts/
RUN cp /scripts/aida/python/aida/logger.py /scripts/
RUN cp /scripts/aida/tools/aida-evaluation/docker/scripts/run_task?_evaluation_pipeline.py /scripts/
RUN cp /scripts/aida/tools/aida-evaluation/docker/scripts/Makefile /scripts/

#-------------------------------------------------------------
# Install SPARQL Evaluation Tool
#-------------------------------------------------------------
# Create directory structure

WORKDIR $SPARQL_EVAL_HOME
RUN mkdir -p config /

# Copy shadow jar and example configuration to sparql-evaluation directory
WORKDIR /scripts/aida/tools/sparql-query-application/docker/AUX-data
RUN cp sparql-evaluation-*-all.jar $SPARQL_EVAL_HOME
RUN cp Local-config.* $SPARQL_EVAL_HOME/config/

# Copy the custom function jar files to inside GraphDB lib
RUN cp rdf4j-function-* ${GRAPHDB_INSTALL_DIR}/lib/

WORKDIR /scripts/

#-------------------------------------------------------------
#  Setup entrypoint
#-------------------------------------------------------------

ENTRYPOINT ["make"]
