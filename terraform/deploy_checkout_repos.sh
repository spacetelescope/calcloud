#! /bin/bash

source deploy_vars.sh

cwd=`pwd`
# setting up the calcloud source dir if it needs downloaded
# equivalent to "if len($var) == 0"
if [ -z "${CALCLOUD_BUILD_DIR}" -o ! -d "${CALCLOUD_BUILD_DIR}" ]
then
    mkdir -p $TMP_INSTALL_DIR
    CALCLOUD_BUILD_DIR="${TMP_INSTALL_DIR}/calcloud"
    export CALCLOUD_BUILD_DIR=$CALCLOUD_BUILD_DIR
    # calcloud source download/unpack
    cd $TMP_INSTALL_DIR
    git clone https://github.com/spacetelescope/calcloud.git
    cd calcloud && git fetch --all --tags
    if git rev-parse -q --verify "refs/tags/v${CALCLOUD_VER}" >/dev/null; then
        git checkout "tags/v${CALCLOUD_VER}"
    elif git rev-parse -q --verify "refs/tags/${CALCLOUD_VER}" >/dev/null; then
        git checkout "tags/${CALCLOUD_VER}"
    else
        echo "could not checkout v${CALCLOUD_VER} or ${CALCLOUD_VER}; exiting"
        exit 1
    fi
    cd ..
fi

# setting up the caldp source dir if it needs downloaded
# equivalent to "if len($var) == 0"
if [ -z "${CALDP_BUILD_DIR}" -o ! -d "${CALDP_BUILD_DIR}" ]
then
    mkdir -p $TMP_INSTALL_DIR
    CALDP_BUILD_DIR="${TMP_INSTALL_DIR}/caldp"
    export CALDP_BUILD_DIR=$CALDP_BUILD_DIR
    cd $TMP_INSTALL_DIR
    # caldp source download/unpack
    # github's tarballs don't work with pip install, so we have to clone and checkout the tag
    git clone https://github.com/spacetelescope/caldp.git
    cd caldp && git fetch --all --tags
    if git rev-parse -q --verify "refs/tags/v${CALDP_VER}" >/dev/null; then
        git checkout "tags/v${CALDP_VER}"
    elif git rev-parse -q --verify "refs/tags/${CALDP_VER}" >/dev/null; then
        git checkout "tags/${CALDP_VER}"
    else
        echo "could not checkout v${CALDP_VER} or ${CALDP_VER}; exiting"
        exit 1
    fi
    cd ..
fi

chmod -R og+r ${TMP_INSTALL_DIR}
find ${TMP_INSTALL_DIR} -type d -exec chmod og+x {} +

cd $cwd
