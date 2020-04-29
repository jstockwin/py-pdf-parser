FROM phusion/baseimage:0.11

RUN adduser --disabled-password --gecos "" app_user

RUN apt-get update && \
    apt-get -y install software-properties-common \
    python3-dev \
    python3-pip

RUN pip3 install --upgrade pip

# Create src dir
ENV PROJECT_DIR /py-pdf-parser

WORKDIR $PROJECT_DIR
ADD ./ $PROJECT_DIR
ADD ./imagemagick_policy.xml /etc/ImageMagick-6/policy.xml

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN chown -R app_user: $PROJECT_DIR

RUN pip3 install $PROJECT_DIR

USER app_user

RUN echo "alias python=python3" > /home/app_user/.bashrc
