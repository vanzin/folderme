#!/bin/bash

cd "$(dirname $0)"/../

ROOT=$(pwd)
BUILD=build/folderme

rm -rf build
mkdir -p $BUILD
cp -r DEBIAN $BUILD
cd $BUILD

mkdir -p usr/share/applications
cp $ROOT/org.vanzin.folderme.desktop usr/share/applications

mkdir -p usr/share/dbus-1/services
cp $ROOT/org.vanzin.FolderME.service usr/share/dbus-1/services

mkdir -p usr/share/folderme
cp -r $ROOT/src/* usr/share/folderme
rm -rf usr/share/folderme/__pycache__

mkdir -p usr/bin
(cd usr/bin && ln -sf ../share/folderme/folderme)

cd ..
dpkg-deb --build folderme
