#!/usr/bin/env bash
source "$(dirname "$0")/../lib.sh"


echo ''
echo '#######################################################################'
echo '#                          Login to AWS ECR                           #'
echo '#######################################################################'

# Login to AWS ecr
$(aws ecr get-login --region=eu-west-1 --no-include-email)

echo ''
echo '#######################################################################'
echo '#              Pull py-pdf-parser-test:latest image from ECR                #'
echo '#######################################################################'

docker pull $DOCKER_REGISTRY/py-pdf-parser-test:latest

echo ''
echo '#######################################################################'
echo '#                       Docker images pulled                          #'
echo '#######################################################################'
