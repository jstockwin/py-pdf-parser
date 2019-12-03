#!/usr/bin/env bash
source "$(dirname "$0")/../lib.sh"

set -e
PROJECT_DIR=/py-pdf-parser

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
  $PROJECT_DIR/jenkins_scripts/in_docker/test.sh
