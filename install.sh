#!/bin/sh
set -e
apt-get update
apt-get install -y python3 python3-pip
pip3 install --upgrade pip
pip3 install -r requirements.txt
