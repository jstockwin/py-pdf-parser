#!/usr/bin/env bash
source "$(dirname "$0")/../lib.sh"

set -e

echo ''
echo '#######################################################################'
echo '#                  Building py-pdf-parser test container                    #'
echo '#######################################################################'
PROJECT_DIR=/py-pdf-parser

docker build . -f $WORKSPACE/dockerfiles/Dockerfile_tests -t py-pdf-parser:test

echo ''
echo '#######################################################################'
echo '#                       Running tests container                       #'
echo '#######################################################################'
docker run --rm \
  --name py_pdf_parser_tests_${GIT_BRANCH}_${BUILD_NUMBER} \
  --env "GIT_BRANCH=$GIT_BRANCH" \
  --env "PROJECT_DIR=$PROJECT_DIR" \
  --volume $WORKSPACE:$PROJECT_DIR \
  py-pdf-parser:test \
  $PROJECT_DIR/jenkins_scripts/in_docker/lint.sh
