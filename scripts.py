""" Script for adding quotas to database """

import os
import datetime
import logging

from cloudfoundry import CloudFoundry
from models import Quota, QuotaData
from quotas import db


def get_or_create(model, **kwargs):
    """ Mimic Django ORM's get_or_create script: if created returns True """
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance, True


def get_datetime(date_str):
    """ Coverts a date string in the form %Y-%m-%dT%H:%M:%SZ to a python
    Python datetime object """
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").date()


def update_quota_data(quota_model, entity_data):
    """ Add quota data to to database """
    quota_data, data_created = get_or_create(
        model=QuotaData,
        quota=quota_model.guid,
        date_collected=datetime.date.today())
    quota_data.memory_limit = entity_data['memory_limit']
    quota_data.total_routes = entity_data['total_routes']
    quota_data.total_services = entity_data['total_services']
    quota_model.data.append(quota_data)


def update_quota(quota):
    """ Load one quota into database """
    quota_model, quota_created = get_or_create(
        model=Quota,
        guid=quota['metadata']['guid']
    )
    quota_model.url = quota['metadata']['url']
    quota_model.name = quota['entity']['name']
    quota_model.created_at = get_datetime(quota['metadata']['created_at'])
    updated = quota['metadata'].get('updated_at')
    if updated:
        quota_model.updated_at = get_datetime(updated)
    update_quota_data(quota_model=quota_model, entity_data=quota['entity'])
    db.session.merge(quota_model)
    db.session.commit()
    return quota_model


def load_quotas(cf_api):
    """ Load quotas into database """
    quotas = cf_api.get_quotas()
    for quota in quotas:
        update_quota(quota)


def load_data():
    """ Starts the data loading process """
    cf_api = CloudFoundry(
        url=os.getenv('CF_URL'),
        username=os.getenv('CF_USERNAME'),
        password=os.getenv('CF_PASSWORD'))
    logging.info('Starting Data Update')
    load_quotas(cf_api=cf_api)
    logging.info('Data Update Successful')
