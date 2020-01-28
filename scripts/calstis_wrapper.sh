#! /bin/sh

mkdir astropy
export XDG_CONFIG_HOME=$(pwd)
export XDG_CACHE_HOME=$(pwd)

source /home/ec2-user/.bashrc
conda activate hstdp
python retrieve_data.py $*

pwd
ls -la

export CRDS_PATH=$(pwd)/crds_cache
export iref=${CRDS_PATH}/references/hst/iref/
export jref=${CRDS_PATH}/references/hst/jref/
export oref=${CRDS_PATH}/references/hst/oref/
export lref=${CRDS_PATH}/references/hst/lref/
export nref=${CRDS_PATH}/references/hst/nref/
export uref=${CRDS_PATH}/references/hst/uref/
export uref_linux=$uref
export CRDS_SERVER_URL=https://hst-serverless.stsci.edu
export CRDS_S3_ENABLED=1
export CRDS_S3_RETURN_URI=0
export CRDS_MAPPING_URI=s3://dmd-test-crds/mappings/hst
export CRDS_REFERENCE_URI=s3://dmd-test-crds/references/hst
export CRDS_CONFIG_URI=s3://dmd-test-crds/config/hst
export CRDS_USE_PICKLES=0
export CRDS_DOWNLOAD_MODE=plugin
export CRDS_DOWNLOAD_PLUGIN='crds_s3_get ${SOURCE_URL} ${OUTPUT_PATH} ${FILE_SIZE} ${FILE_SHA1SUM}'

crds bestrefs --update-bestrefs --sync-references=1 --files *_raw.fits
crds bestrefs --update-bestrefs --sync-references=1 --files *_tag.fits
crds bestrefs --update-bestrefs --sync-references=1 --files *_wav.fits

if test -f "${*}_raw.fits"; then
    cs0.e -tv "${*}_raw.fits" 2>&1 | tee -a "${*}.tra"
else
    cs0.e -tv "${*}_wav.fits" 2>&1 | tee -a "${*}.tra"
fi

mkdir $*
mv *.fits $*
mv *.tra $*
cp ALOG* $*
cp *condor* $*
aws s3 cp $* s3://bhayden-hstcal/$* --recursive
rm -rf ./$*
rm -rf ./astropy/
