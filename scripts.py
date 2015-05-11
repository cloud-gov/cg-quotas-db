import os
import datetime
from cloudfoundry import CloudFoundry
from models import Org
from quotas import db

""" App scripts """


def get_datetime(date_str):
    """ Coverts a date string in the form %Y-%m-%dT%H:%M:%SZ to a python
    Python datetime object """
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").date()


def update_quota(org):
    """ Load one org quota into database """
    o = Org(
        guid=org['metadata']['guid'],
        name=org['entity']['name'],
        url=org['metadata']['url'])
    o.memory_limit = org['entity']['memory_limit']
    o.total_routes = org['entity']['total_routes']
    o.total_services = org['entity']['total_services']
    o.created_at = get_datetime(org['metadata']['created_at'])
    updated = org['metadata'].get('updated_at')
    if updated:
        o.updated_at = get_datetime(updated)
    db.session.merge(o)
    db.session.commit()


def load_quotas():
    """ Load quotas into database """
    cf_api = CloudFoundry(
        url=os.getenv('CF_URL'),
        username=os.getenv('CF_USERNAME'),
        password=os.getenv('CF_PASSWORD'))
    data = cf_api.get_quotas()

    for org in data['resources']:
        if org['entity'].get('name'):
            update_quota(org)
