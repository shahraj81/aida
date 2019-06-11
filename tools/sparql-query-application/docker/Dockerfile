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
#  Install GraphDB
#  Taken from the Dockerfile for GraphDB docker available at:
#  https://github.com/Ontotext-AD/graphdb-docker
#-------------------------------------------------------------
# Define arguments need for installation of GraphDB

ARG version=8.9.0
ARG edition=free

ENV GRAPHDB_PARENT_DIR=/opt/graphdb
ENV GRAPHDB_HOME=${GRAPHDB_PARENT_DIR}/home

ENV GRAPHDB_INSTALL_DIR=${GRAPHDB_PARENT_DIR}/dist

COPY ./AUX-data/graphdb-${edition}-${version}-dist.zip /tmp/

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
# Copy required scripts
COPY ./scripts /scripts
ENTRYPOINT ["make", "-f" , "/scripts/Makefile"]

#-------------------------------------------------------------
# Install SPARQL Evaluation Tool
#-------------------------------------------------------------
# Create directory structure
ENV SPARQL_EVAL_HOME /opt/sparql-evaluation
WORKDIR $SPARQL_EVAL_HOME
RUN mkdir -p config /

# Copy shadow jar and example configuration to sparql-evaluation directory
COPY ./AUX-data/sparql-evaluation-*-all.jar $SPARQL_EVAL_HOME
COPY ./AUX-data/Local-config.* $SPARQL_EVAL_HOME/config/

# Copy the custom function jar files to inside GraphDB lib
COPY ./AUX-data/rdf4j-function-* ${GRAPHDB_INSTALL_DIR}/lib/
