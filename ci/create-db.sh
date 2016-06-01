#!/bin/bash

set -e -x

cf login -a $CF_API_URL -u $CF_DEPLOY_USERNAME -p $CF_DEPLOY_PASSWORD -o $CF_ORGANIZATION -s $CF_SPACE

# Create database service instance if not exists
if ! cf service $SERVICE_NAME ; then
  cf create-service aws-rds $SERVICE_PLAN $SERVICE_NAME
fi
