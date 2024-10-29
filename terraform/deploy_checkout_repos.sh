#! /bin/bash

source deploy_vars.sh

cwd=`pwd`
# setting up the calcloud source dir if it needs downloaded
# equivalent to "if len($var) == 0"
if [ -z "${CALCLOUD_BUILD_DIR}" ]
then
    mkdir -p $TMP_INSTALL_DIR
    CALCLOUD_BUILD_DIR="${TMP_INSTALL_DIR}/calcloud"
    export CALCLOUD_BUILD_DIR=$CALCLOUD_BUILD_DIR
    # calcloud source download/unpack
    cd $TMP_INSTALL_DIR
    git clone https://github.com/spacetelescope/calcloud.git
    cd calcloud && git fetch --all --tags && git checkout tags/v${CALCLOUD_VER} && cd ..
    git_exit_status=$?
    if [[ $git_exit_status -ne 0 ]]; then
        # try without the v
        cd calcloud && git fetch --all --tags && git checkout tags/${CALCLOUD_VER} && cd ..
        git_exit_status=$?
    fi
    if [[ $git_exit_status -ne 0 ]]; then
        echo "could not checkout ${CALCLOUD_VER}; exiting"
        exit 1
    fi
fi

# setting up the caldp source dir if it needs downloaded
# equivalent to "if len($var) == 0"
if [ -z "${CALDP_BUILD_DIR}" ]
then
    mkdir -p $TMP_INSTALL_DIR
    CALDP_BUILD_DIR="${TMP_INSTALL_DIR}/caldp"
    export CALDP_BUILD_DIR=$CALDP_BUILD_DIR
    cd $TMP_INSTALL_DIR
    # caldp source download/unpack
    # github's tarballs don't work with pip install, so we have to clone and checkout the tag
    git clone https://github.com/spacetelescope/caldp.git
    cd caldp && git fetch --all --tags && git checkout tags/v${CALDP_VER} && cd ..
    git_exit_status=$?
    if [[ $git_exit_status -ne 0 ]]; then
        # try without the v
        cd caldp && git fetch --all --tags && git checkout tags/${CALDP_VER} && cd ..
        git_exit_status=$?
    fi
    if [[ $git_exit_status -ne 0 ]]; then
        echo "could not checkout ${CALDP_VER}; exiting"
        exit 1
    fi
fi

chmod -R og+r ${TMP_INSTALL_DIR}
find ${TMP_INSTALL_DIR} -type d -exec chmod og+x {} +

cd $cwd
