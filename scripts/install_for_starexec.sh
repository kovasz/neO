#!/bin/bash

yum -y update
yum -y install centos-release-scl
yum -y install epel-release

# yum install rh-python38 rh-python38-python-devel
# scl enable rh-python38 bash
# pip3 install numpy parse wheel pathos python-sat pysmt

yum -y install python36 python36-devel python36-pip

pip3 install setuptools numpy parse wheel pathos python-sat

pip3 install -Iv pysmt==0.8.0
pysmt-install --confirm-agreement --z3
pysmt-install --confirm-agreement --yices

pip3 install pyinstaller
