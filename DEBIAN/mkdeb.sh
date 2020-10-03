#!/bin/bash

cd "$(dirname $0)"/../

ROOT=$(pwd)
BUILD=build/folderme

rm -rf build
mkdir -p $BUILD
cp -r DEBIAN $BUILD
cd $BUILD

mkdir -p usr/bin
mkdir -p usr/share/folderme
mkdir -p usr/share/applications

cp -r $ROOT/src/* usr/share/folderme
cp $ROOT/org.vanzin.folderme.desktop usr/share/applications
(cd usr/bin && ln -sf ../share/folderme/folderme)
rm -rf usr/share/folderme/__pycache__

cd ..
dpkg-deb --build folderme
