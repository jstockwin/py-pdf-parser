if [[ -z $DOCKER_REGISTRY ]]; then
  DOCKER_REGISTRY=069140875175.dkr.ecr.eu-west-1.amazonaws.com
fi

if [[ -z $WORKSPACE ]]; then
  WORKSPACE=$(pwd)
fi

if [[ -z $BRANCH_NAME ]]; then
  GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
else
  GIT_BRANCH=$BRANCH_NAME
fi

GIT_BRANCH=${GIT_BRANCH#*/}

build_docker_image() {
  image=$1
  dockerfile=$2

  echo ""
  echo "-----"
  echo "BUILDING $image:$GIT_BRANCH using $dockerfile"
  echo "-----"

  BUILD_DIR="docker_build_$image"

  rm -rf "$BUILD_DIR"
  git clone . "$BUILD_DIR" || exit 1
  cd "$BUILD_DIR"

  # clean up

  rm -rf .git

  # build the image

  docker build \
      -t $DOCKER_REGISTRY/$image:$GIT_BRANCH \
      -f $dockerfile \
      . || exit 1

  cd $WORKSPACE
  rm -rf "$BUILD_DIR"
}

tag_docker_image() {
    image=$1
    tag=${2:-latest}

    echo "Tagging $DOCKER_REGISTRY/$image:$GIT_BRANCH"
    echo "     as $DOCKER_REGISTRY/$image:$tag"
    docker tag $DOCKER_REGISTRY/$image:$GIT_BRANCH $DOCKER_REGISTRY/$image:$tag
}

push_docker_image() {
    image=$1
    tag=${2:-$GIT_BRANCH}

    echo "Pushing $DOCKER_REGISTRY/$image:$tag"
    docker push $DOCKER_REGISTRY/$image:$tag
}
