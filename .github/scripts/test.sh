#!/bin/bash

clean_pyc () { echo 'cleaning .pyc files'; find . -name "*.pyc" -exec rm -f {} \; ; }
trap clean_pyc EXIT

echo ''
echo '#######################################################################'
echo '#                          Running nosetests                          #'
echo '#######################################################################'
nosetests $PROJECT_DIR

TEST_STATUS=$?
if [[ ("$TEST_STATUS" == 0) ]]; then
  echo '#######################################################################'
  echo '#                          nosetests succeded                         #'
  echo '#######################################################################'
  exit 0
else
  echo ''
  echo '#######################################################################'
  echo '#                          nosetests failed    !                      #'
  echo '#######################################################################'
  exit 1
fi
