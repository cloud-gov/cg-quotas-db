#!/bin/sh

set -e -x

cd cg-quotas-db

pip install -r requirements-dev.txt
export APP_SETTINGS="config.TestingConfig"
nosetests
