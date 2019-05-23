FROM ubuntu:18.04
MAINTAINER shahzad.rajput@nist.gov

# Install system packages
RUN apt-get update && apt-get install -y \
    curl \
    git \
    make \
    wget \
    perlbrew \
    unzip

ENV HOME /root
ENV PERLBREW_PATH=$HOME/perl5/perlbrew/bin

# Install cpanm
RUN perlbrew install-cpanm

# Install Json
RUN $PERLBREW_PATH/cpanm install JSON

#Create directory structure
ENV SCRIPTS /opt/scripts
RUN mkdir -p $SCRIPTS
WORKDIR $SCRIPTS

# Pull AIDA Git Repository
WORKDIR /tmp
RUN git clone https://github.com/shahraj81/aida.git -b AIDACA-v2019.0.1
WORKDIR /tmp/aida/tools/confidence-aggregation/
RUN perl Include.pl AIDA-ConfidenceAggregation-MASTER.pl > $SCRIPTS/AIDA-ConfidenceAggregation.pl

WORKDIR $SCRIPTS

CMD perl AIDA-ConfidenceAggregation.pl TA1_GR /mnt/input /mnt/output
