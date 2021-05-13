# syntax = docker/dockerfile:1.2
FROM phusion/baseimage:focal-1.0.0

RUN adduser --disabled-password --gecos "" app_user
RUN echo "alias python=python3" > /home/app_user/.bashrc

RUN apt-get update && \
    apt-get -y install software-properties-common \
                       python3-dev \
                       python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN --mount=type=cache,target=/root/.cache/pip pip3 install --upgrade pip

# Create src dir
ENV PROJECT_DIR /py-pdf-parser
WORKDIR $PROJECT_DIR

# Add imagemagick policy
ADD ./imagemagick_policy.xml /etc/ImageMagick-6/policy.xml

# Install requirements
ADD ./setup.py $PROJECT_DIR/setup.py
ADD ./README.md $PROJECT_DIR/README.md
RUN --mount=type=cache,target=/root/.cache/pip pip3 install -e $PROJECT_DIR

# Copy code, chown and switch user
ADD ./ $PROJECT_DIR
RUN chown -R app_user: $PROJECT_DIR
USER app_user
