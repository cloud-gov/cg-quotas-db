#!/bin/bash
echo "------ Starting APP ------"
if [ $CF_INSTANCE_INDEX = "0" ]; then
    echo "----- Apply Migrations -----"
    python manage.py db upgrade
    echo "----- build app ------"
    python manage.py build
fi
gunicorn quotas:app --log-file -
