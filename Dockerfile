FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    curl \
    git \
    mesa-common-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /root
RUN curl -L -o mambaforge.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh"
RUN bash mambaforge.sh -b -p $HOME/mambaforge
RUN rm mambaforge.sh

RUN . /root/mambaforge/bin/activate \
    && mamba init \
    && mamba create -y -n cq \
        python \
        cadquery \
        fastapi \
        uvicorn \
        jinja2 \
        shapely \
    && mamba clean -a -y

RUN echo "source /root/mambaforge/bin/activate" >> /root/.bashrc
RUN echo "mamba activate cq" >> /root/.bashrc

ENTRYPOINT ["/bin/bash", "-l", "-c"]