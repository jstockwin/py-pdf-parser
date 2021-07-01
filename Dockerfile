# syntax = docker/dockerfile:1.2
FROM phusion/baseimage:focal-1.0.0

RUN adduser --disabled-password --gecos "" app_user

RUN apt-get update && \
    apt-get -y install software-properties-common \
                       python3-pip \
                       python3-virtualenv \
                       python3-tk \
                       libmagickwand-dev \
                       xvfb && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV VIRTUAL_ENV_DIR /.venv
RUN python3 -m virtualenv --python=python3.8 $VIRTUAL_ENV_DIR
# Set the virtual environment as the main Python directory
ENV PATH $VIRTUAL_ENV_DIR/bin:$PATH

RUN --mount=type=cache,target=/root/.cache/pip pip3 install --upgrade pip

# Create src dir
ENV PROJECT_DIR /py-pdf-parser
WORKDIR $PROJECT_DIR

# Add imagemagick policy
ADD ./imagemagick_policy.xml /etc/ImageMagick-6/policy.xml

# Install requirements
ADD ./setup.py $PROJECT_DIR/setup.py
ADD ./README.md $PROJECT_DIR/README.md
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -e $PROJECT_DIR[dev]
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -e $PROJECT_DIR[test]
RUN chown -R app_user:app_user $VIRTUAL_ENV_DIR

# Copy code, chown and switch user
ADD ./ $PROJECT_DIR
RUN chown -R app_user:app_user $PROJECT_DIR
USER app_user
