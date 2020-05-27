FROM ubuntu:18.04
MAINTAINER shahzad.rajput@nist.gov

# Install system packages
RUN apt-get update && apt-get install -y \
    curl \
    git \
    make \
    python3 \
    unzip \
    perlbrew \
    vim

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

ARG version=8.2.1
ARG edition=free

ENV GRAPHDB_PARENT_DIR=/opt/graphdb
ENV GRAPHDB_HOME=${GRAPHDB_PARENT_DIR}/home
ENV GRAPHDB_INSTALL_DIR=${GRAPHDB_PARENT_DIR}/dist
ENV SPARQL_EVAL_HOME=/opt/sparql-evaluation
ENV PATH=${GRAPHDB_INSTALL_DIR}/bin:$PATH

RUN mkdir scripts
RUN mkdir AUX-data

COPY ./AUX-data/graphdb-${edition}-${version}-dist.zip /tmp/
COPY ./AUX-data/queries /queries
COPY ./scripts/run.py /scripts/
COPY ./scripts/logger.py /scripts/
COPY ./scripts/log_specifications.txt /scripts/
COPY ./scripts/aida /scripts/aida
COPY ./AUX-data/LDC2019E42* /AUX-data/
COPY ./AUX-data/LDC2019R30_AIDA_Phase_1_Assessment_Results_V6.1 /AUX-data/LDC2019R30_AIDA_Phase_1_Assessment_Results_V6.1
COPY ./AUX-data/task1_*_queryids.txt /AUX-data/

WORKDIR /tmp

RUN mkdir -p ${GRAPHDB_PARENT_DIR} && \
    cd ${GRAPHDB_PARENT_DIR} && \
    unzip /tmp/graphdb-${edition}-${version}-dist.zip && \
    rm /tmp/graphdb-${edition}-${version}-dist.zip && \
    mv graphdb-${edition}-${version} dist && \
    mkdir -p ${GRAPHDB_HOME}

RUN mkdir $SPARQL_EVAL_HOME



ENV PERLBREW_PATH=/root/perl5/perlbrew/bin
RUN perlbrew install-cpanm
RUN $PERLBREW_PATH/cpanm install JSON

# Setup the AIDA repository

WORKDIR /scripts/aida

RUN git checkout AIDAQA-v2019.2.5

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

ENTRYPOINT ["python3", "run.py"]
#ENTRYPOINT ["make", "-f" , "/scripts/Makefile"]
#ENTRYPOINT ["/bin/bash"]
