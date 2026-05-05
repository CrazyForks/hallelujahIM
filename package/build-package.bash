#!/bin/bash

## PKG_POSTINSTALL_ACTION=logout bash package/build-package.bash

set -e

cd "$(dirname $0)"
PROJECT_ROOT=$(cd ..; pwd)

Version=`date "+%Y%m%d%H%M%S"`
GitHash=`git -C "${PROJECT_ROOT}" rev-parse --short HEAD`

pushd ${PROJECT_ROOT}
sh build.sh
popd

rm -f /tmp/hallelujah-*.pkg
rm -rf /tmp/hallelujah/build/release/root/
mkdir -p /tmp/hallelujah/build/release/root
cp -R /tmp/hallelujah/build/release/hallelujah.app /tmp/hallelujah/build/release/root/


# Allow overriding postinstall-action via env var (e.g. PKG_POSTINSTALL_ACTION=logout)
POSTINSTALL_ACTION="${PKG_POSTINSTALL_ACTION:-none}"
sed "s/__POSTINSTALL_ACTION__/${POSTINSTALL_ACTION}/" \
    "${PROJECT_ROOT}/package/PackageInfo" \
    > /tmp/hallelujah/build/release/PackageInfo

pkgbuild \
    --info /tmp/hallelujah/build/release/PackageInfo \
    --root "/tmp/hallelujah/build/release/root" \
    --identifier "github.dongyuwei.inputmethod.hallelujahInputMethod" \
    --version ${Version} \
    --install-location "/Library/Input Methods" \
    --scripts "${PROJECT_ROOT}/package/scripts" \
    /tmp/hallelujah-${Version}-${GitHash}.pkg
