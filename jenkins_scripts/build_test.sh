#!/bin/bash
source "$(dirname "$0")/lib.sh"

$(aws ecr get-login --region=eu-west-1  | sed -e "s/-e none//g")

# get the tag from the git revision
TAG="$(git describe --tags --match '*test/*' | sed 's:.*test/::')"

build_docker_image py-pdf-parser-test dockerfiles/Dockerfile_tests

tag_docker_image py-pdf-parser-test $TAG
push_docker_image py-pdf-parser-test $TAG

tag_docker_image py-pdf-parser-test latest
push_docker_image py-pdf-parser-test latest
