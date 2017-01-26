#!/bin/bash

set -e

pushd cg-quotas-db-src
  npm install
  npm run build
popd

cp -r cg-quotas-db-src/* cg-quotas-db-src-assets
