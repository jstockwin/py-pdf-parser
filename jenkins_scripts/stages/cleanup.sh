#!/bin/bash

# Cleanup docker images if branch no longer exists on github

if [[ -z $DOCKER_REGISTRY ]]; then
  DOCKER_REGISTRY=069140875175.dkr.ecr.eu-west-1.amazonaws.com
fi

TAG_REGEXP='[[:digit:]]\{4\}\.[[:digit:]]\{2\}\.[[:digit:]]\{2\}\.[[:digit:]]\{2\}\.[[:digit:]]\{2\}\.[[:digit:]]\{2\}$'

cleanup_images() {
  image_name=$1
  echo "CLEANING $image_name"
  docker images|grep "$image_name\>" |
  {
    while read image; do
      image_tag=$(echo "$image" | awk '{print $2}')

      if [[ -n $(echo $image_tag | grep $TAG_REGEXP) ]]; then
        echo "keeping tag $image_tag"
        continue
      fi

      if [[ $image_tag = 'latest' ]]; then
        echo "keeping tag latest"
        continue
      fi

      found=0
      for branch in $(git branch -r); do
        # strip origin/
        git_branch=${branch#*/}

        if [[ $git_branch = $image_tag ]]; then
          found=1
          break
        fi
      done

      if [[ $found = 0 ]]; then
        echo "NO MATCH -- rmi $image_tag"
        docker rmi $DOCKER_REGISTRY/$image_name:$image_tag || true
      fi
    done
  }
}

echo ''
echo '#######################################################################'
echo '#                 Tests finished, now doing cleanup                   #'
echo '#######################################################################'

echo ''
echo '#######################################################################'
echo '#         Removing images for branches that no longer exist           #'
echo '#######################################################################'

cleanup_images reports-test

echo ''
echo '#######################################################################'
echo '#                      Removing dangling images                       #'
echo '#######################################################################'
docker rmi $(docker images -f 'dangling=true' -q) || true
