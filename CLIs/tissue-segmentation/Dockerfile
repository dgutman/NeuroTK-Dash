FROM pytorch/pytorch:latest
# FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime
# FROM jvizcar/braak-study:latest

USER root

# This tells girder_worker to enable gpu if possible
LABEL com.nvidia.volumes.needed=nvidia_driver

RUN python -m pip install histomicstk --find-links https://girder.github.io/large_image_wheels
RUN python -m pip install girder-client girder-slicer-cli-web h5py

# Install git to clone NeuroTK-Dash repo.
RUN apt update
RUN apt install -y git

RUN mkdir /opt/scw
RUN git clone https://github.com/dgutman/NeuroTK-Dash.git /opt/scw/NeuroTK-Dash
COPY . /opt/scw
WORKDIR /opt/scw/cli

ENV PYTHONUNBUFFERED=TRUE

ENTRYPOINT ["/bin/bash", "docker-entrypoint.sh"]
