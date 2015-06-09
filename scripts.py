import os
import datetime
import logging

from cloudfoundry import CloudFoundry
from models import Quota, QuotaData, Service
from quotas import db


""" App scripts """


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
        guid=quota['metadata']['guid'],
        name=quota['entity']['name'],
        url=quota['metadata']['url'])
    quota_model.created_at = get_datetime(quota['metadata']['created_at'])
    updated = quota['metadata'].get('updated_at')
    if updated:
        quota_model.updated_at = get_datetime(updated)
    update_quota_data(quota_model=quota_model, entity_data=quota['entity'])
    db.session.merge(quota_model)
    db.session.commit()
    return quota_model


def load_services(space_summary, quota):
    """ Load services into database """
    services = space_summary.get('services')
    for service in services:
        if 'service_plan' in service:
            service_instance, created = get_or_create(
                model=Service,
                quota=quota.guid,
                guid=service['service_plan']['service']['guid'],
                instance_name=service['service_plan']['name'],
                label=service['service_plan']['service']['label'],
                provider=service['service_plan']['service']['provider'],
                date_collected=datetime.date.today())
            service_instance.user_defined = True
            quota.services.append(service_instance)
            db.session.merge(quota)
            db.session.commit()


def process_spaces(cf_api, spaces_url, quota):
    """ Extracts services from each space """
    spaces_gen = cf_api.yield_request(endpoint=spaces_url)
    for page in spaces_gen:
        for space in page['resources']:
            space_url = '%s/summary' % space['metadata']['url']
            space_summary = cf_api.make_request(endpoint=space_url).json()
            load_services(space_summary=space_summary, quota=quota)


def process_org(cf_api, org):
    """ Extracts quota data from org, calls api, and updates data """
    quota_definition_url = org['entity']['quota_definition_url']
    quota = cf_api.make_request(endpoint=quota_definition_url)
    quota_model = update_quota(quota.json())
    spaces_url = org['entity']['spaces_url']
    process_spaces(cf_api=cf_api, spaces_url=spaces_url, quota=quota_model)


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
