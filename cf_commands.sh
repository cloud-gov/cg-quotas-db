#!/bin/bash
echo "------ Starting APP ------"
if [ $CF_INSTANCE_INDEX = "0" ]; then
    echo "----- Apply Migrations -----"
    python manage.py db upgrade
    echo "----- Load Database -----"
    python manage.py update_database
    echo "----- build app ------"
    python manage.py build
fi
gunicorn quotas:app --log-file -
