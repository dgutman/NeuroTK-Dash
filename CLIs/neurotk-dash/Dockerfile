FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

# Make non-interactive
ARG DEBIAN_FRONTEND=noninteractive

USER root

# This tells girder_worker to enable gpu if possible
LABEL com.nvidia.volumes.needed=nvidia_driver

RUN python -m pip install histomicstk --find-links https://girder.github.io/large_image_wheels
RUN python -m pip install girder-client girder-slicer-cli-web h5py

# Install git to clone NeuroTK-Dash repo.
RUN apt update
RUN apt install -y git
RUN apt-get install ffmpeg libsm6 libxext6 -y

RUN mkdir /opt/scw
RUN git clone https://github.com/dgutman/NeuroTK-Dash.git /opt/scw/NeuroTK-Dash
COPY . /opt/scw
WORKDIR /opt/scw/cli

# Install additional Python libraries.
RUN pip install ultralytics
RUN pip install geopandas

ENV PYTHONUNBUFFERED=TRUE

# ENTRYPOINT ["/bin/bash", "docker-entrypoint.sh"]
