#!/bin/sh

if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root." 1>&2
    exit 1   
fi

echo "Building Debian package inside $(pwd)..."
#echo "You might want to delete the 'deb' folder afterwards."

mkdir -p deb/usr/share
mkdir -p deb/usr/lib/python3/dist-packages/scff
mkdir -p deb/usr/doc/scff

cp -r bin/ deb/usr/
cp -r data/* deb/usr/share
cp -r scff/* deb/usr/lib/python3/dist-packages/scff

chown -R root:root deb/usr
chmod -R 755 deb/usr/
chmod 644 deb/usr/share/man/man1/*
chmod 644 deb/usr/share/bash-completion/*
chmod 644 deb/usr/share/zsh/vendor-completions/*
chmod 644 deb/usr/share/scff/roving.tar.gz
chmod 644 deb/usr/share/scff/mark-redundant.patch
chmod 644 deb/usr/share/scff/testcase

mkdir -p deb/DEBIAN

cat > deb/DEBIAN/control <<EOF
Package: scff
Section: misc
Priority: optional
Maintainer: softscheck <wilfried.kirsch@softscheck.com>
Build-Depends: debhelper (>=9)
Standards-Version: 3.9.6
Homepage: https://github.com/softscheck/scff
Architecture: all
Suggests: gdb, afl
Version: 0.42
Installed-Size: 4400
Depends: python3, python3-boto3, openssh-client
Description: softScheck Cloud Fuzzing Framework
 A sophisticated Cloud Fuzzing Framework, which makes fuzzing in the cloud easy.
 Things scff does for you:
    * Create multiple Amazon instances at once using a simple config file
    * List Amazon instances
    * Group Amazon instances
    * Control groups up to hundreds of instances with only one command
    * Control fuzzers running in these groups
    * Retrieve reports/status of machines and fuzzers
    * Check if findings contain any false reports
    * Examine findings
EOF

cat > deb/usr/doc/scff/copyright <<EOF
Format: http://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: softScheck Cloud Fuzzing Framework
Upstream-Contact: Wilfried Kirsch <wilfried.kirsch@softscheck.com>
Source: https://github.com/softscheck/scff/

Files: *
Copyright: 2017 Wilfried Kirsch
License: GPL-3

Files: usr/share/scff/roving.tar.gz
Copyright: 2015 Richo Healey <richo@psych0tik.net>
License: MITc
EOF

dpkg-deb --build deb scff.deb

rm -r deb

