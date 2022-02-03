FROM ubuntu:18.04
MAINTAINER shahzad.rajput@nist.gov

# Set timezone
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime

# Install system packages
RUN apt-get update && apt-get install -y \
    curl \
    git \
    make \
    unzip \
    perlbrew \
    tzdata \
    vim

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
#  Upgrade python to version 3.9.0
#-------------------------------------------------------------

RUN apt-get install build-essential checkinstall -y
RUN apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev \
    libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev liblzma-dev wget -y
WORKDIR /opt
RUN wget https://www.python.org/ftp/python/3.9.2/Python-3.9.2.tgz
RUN tar xzf Python-3.9.2.tgz
WORKDIR /opt/Python-3.9.2
RUN ./configure --enable-optimizations
RUN make altinstall
WORKDIR /opt
RUN rm -rf Python-3.9.2.tgz Python-3.9.2

#-------------------------------------------------------------
# Upgrade pip and install munkres
#-------------------------------------------------------------

RUN python3.9 -m pip install --upgrade pip

#-------------------------------------------------------------
# Install munkres
#-------------------------------------------------------------

RUN pip3.9 install munkres

#-------------------------------------------------------------
#  Install awscli
#-------------------------------------------------------------

RUN pip3.9 --no-cache-dir install --upgrade awscli

#-------------------------------------------------------------
#  Install arch
#-------------------------------------------------------------

RUN pip3.9 install arch

#-------------------------------------------------------------
#  Install numpy
#-------------------------------------------------------------

RUN pip3.9 install numpy

#-------------------------------------------------------------
#  Install GraphDB
#  Taken from the Dockerfile for GraphDB docker available at:
#  https://github.com/Ontotext-AD/graphdb-docker
#-------------------------------------------------------------
# Define arguments need for installation of GraphDB

ARG version=9.10.2
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

RUN git clone -b AIDAED-v2022.0.3 https://github.com/shahraj81/aida.git

WORKDIR /scripts/aida

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
