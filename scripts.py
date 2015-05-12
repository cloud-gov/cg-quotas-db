import os
import datetime
from cloudfoundry import CloudFoundry
from models import Quota, QuotaData
from quotas import db

""" App scripts """


def get_or_create(model, **kwargs):
    """ Mimic Django ORM's get_or_create script """
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, True
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance, False


def get_datetime(date_str):
    """ Coverts a date string in the form %Y-%m-%dT%H:%M:%SZ to a python
    Python datetime object """
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").date()


def update_quota(quota):
    """ Load one quota into database """
    q, quota_created = get_or_create(
        model=Quota,
        guid=quota['metadata']['guid'],
        name=quota['entity']['name'],
        url=quota['metadata']['url'])
    q.created_at = get_datetime(quota['metadata']['created_at'])
    updated = quota['metadata'].get('updated_at')
    if updated:
        q.updated_at = get_datetime(updated)
    quota_data, data_created = get_or_create(QuotaData, quota_id=q)
    quota_data.memory_limit = quota['entity']['memory_limit']
    quota_data.total_routes = quota['entity']['total_routes']
    quota_data.total_services = quota['entity']['total_services']
    q.data.append(quota_data)
    db.session.merge(q)
    db.session.commit()


def load_quotas():
    """ Load quotas into database """
    cf_api = CloudFoundry(
        url=os.getenv('CF_URL'),
        username=os.getenv('CF_USERNAME'),
        password=os.getenv('CF_PASSWORD'))
    api_gen = cf_api.get_quotas()
    for page in api_gen:
        for quota in page['resources']:
            if quota['entity'].get('name'):
                update_quota(quota)
