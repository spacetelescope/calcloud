# Copyright (c) Association of Universities for Research in Astronomy
# Distributed under the terms of the Modified BSD License.

# DATB's HST CAL code build for the pipeline
FROM astroconda/datb-tc-pipeline:hstdp-snapshot

LABEL maintainer="dmd_octarine@stsci.edu" \
      vendor="Space Telescope Science Institute"

# Environment variables
ENV MKL_THREADING_LAYER="GNU"

USER root

# RUN yum update  -y

RUN yum install -y curl rsync time

# Install hstdp conda environment
# RUN conda create -n hstdp --file http://ssb.stsci.edu/releases/hstdp/2019.5/latest-linux

RUN pip install --upgrade pip
RUN pip install awscli boto3
RUN pip install jupyterlab
RUN pip install --upgrade git+https://github.com/spacetelescope/calcloud.git
RUN pip install spec-plots==1.34.6

# Install fitscut
COPY install-fitscut  .
RUN ./install-fitscut && rm ./install-fitscut

WORKDIR /home/developer
USER developer

