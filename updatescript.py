import os
import datetime
import logging

from cloudfoundry import CloudFoundry
from models import Quota, QuotaData
from quotas import db


def datetime_iterator(from_date, to_date):
    while to_date is None or from_date <= to_date:
        yield from_date
        from_date = from_date + datetime.timedelta(days=1)


def get_datetime(date_str):
    """ Coverts a date string in the form %Y-%m-%dT%H:%M:%SZ to a python
    Python datetime object """
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").date()


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


def update_quota_data(quota_model, entity_data, date):
    """ Add quota data to to database """

    quota_data, data_created = get_or_create(
        model=QuotaData,
        quota=quota_model.guid,
        date_collected=date)
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

    for date in datetime_iterator(
            datetime.date(2015, 7, 9), datetime.date(2015, 7, 16)):
        update_quota_data(
            quota_model=quota_model, entity_data=quota['entity'], date=date)
        db.session.merge(quota_model)
        db.session.commit()

    return quota_model


def process_org(cf_api, org):
    """ Extracts quota data from org, calls api, and updates data """
    quota_definition_url = org['entity']['quota_definition_url']
    quota = cf_api.make_request(endpoint=quota_definition_url)
    update_quota(quota.json())


def load_quotas(cf_api):
    """ Load quotas into database """
    api_gen = cf_api.get_orgs()
    for page in api_gen:
        for org in page['resources']:
            process_org(cf_api=cf_api, org=org)


def load_data():
    """ Starts the data loading process """
    cf_api = CloudFoundry(
        url=os.getenv('CF_URL'),
        username=os.getenv('CF_USERNAME'),
        password=os.getenv('CF_PASSWORD'))
    logging.info('Starting Data Update')
    load_quotas(cf_api=cf_api)
    logging.info('Data Update Successful')
