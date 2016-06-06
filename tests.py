# Extral Imports
from unittest import mock
from flask.ext.testing import TestCase
import base64
import copy
import datetime
import requests
import types
import unittest

# App imports
from cloudfoundry import CloudFoundry
from quotas import app, db
from models import Quota, QuotaData
from api import QuotaResource, QuotaDataResource
import scripts

# Auth testings
from config import Config
from werkzeug.test import Client
from werkzeug.datastructures import Headers

# Flip app settings to testing
app.config.from_object('config.TestingConfig')

mock_quota = {
    'metadata': {
        'created_at': '2015-01-01T01:01:01Z',
        'guid': 'test_quota',
        'total_routes': 5,
        'updated_at': '2015-01-01T01:01:01Z',
        'url': '/v2/quota_definitions/test'
    },
    'entity': {
        'name': 'test_quota_name',
        'memory_limit': 1875,
        'total_routes': 5,
        'total_services': 2
    }
}
mock_quota_2 = copy.deepcopy(mock_quota)
mock_quota_2['metadata']['guid'] = 'test_quota_2'
mock_quotas_data = {
    'next_url': None,
    'resources': [mock_quota, mock_quota_2]
}
mock_org_data = {
    'next_url': None,
    'resources': [
        {
            "entity": {
                "quota_definition_url": "/v2/quota_definitions/f7963421",
                "spaces_url": "/v2/organizations/f190f9a3/spaces",
            }
        },
        {
            "entity": {
                "quota_definition_url": "/v2/quota_definitions/guid_2",
                "spaces_url": "/v2/organizations/org_1/spaces",
            }
        }
    ]
}
mock_space_summary = {
    'services': [
        {'service_plan': {
            'name': 'instance_1',
            'service': {
                'guid': 'guid_1',
                'label': 'plan_label_1',
                'provider': 'core'
            },
        }},
        {'service_plan': {
            'name': 'instance_1',
            'service': {
                'guid': 'guid_2',
                'label': 'plan_label_2',
                'provider': 'core'
            },
        }},
    ]
}

mock_token_data = {'access_token': '999', 'expires_in': 0}


class MockReq:
    """ Returns a mock token in json form """
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def mock_token(func):
    """ Patches post request and return a mock token """
    def test_mock_token(*args, **kwargs):
        with mock.patch.object(
                requests, 'post', return_value=MockReq(data=mock_token_data)):
            return func(*args, **kwargs)
    return test_mock_token


def mock_quotas_request(func):
    """ Patches get request and return mock quota definitions """
    def test_mock_get(*args, **kwargs):
        with mock.patch.object(
                requests, 'get',
                return_value=MockReq(data=mock_quotas_data)):
            return func(*args, **kwargs)
    return test_mock_get


def mock_orgs_request(func):
    """ Patches get request and return mock quota definitions """
    def test_mock_get(*args, **kwargs):
        with mock.patch.object(
                requests, 'get',
                return_value=MockReq(data=mock_org_data)):
            return func(*args, **kwargs)
    return test_mock_get


class CloudFoundryTest(unittest.TestCase):
    """ Test CloudFoundry client """

    @mock_token
    def setUp(self):
        self.cf = CloudFoundry(
            uaa_url='login.test.com',
            api_url='api.test.com',
            username='mockusername@mock.com',
            password='******')

    @mock_token
    def test_init(self):
        """ Test that CloudFoundry object initializes properly """

        self.assertEqual(self.cf.api_url, 'api.test.com')
        self.assertEqual(self.cf.username, 'mockusername@mock.com')
        self.assertEqual(self.cf.password, '******')
        self.assertEqual(self.cf.token['access_token'], '999')
        self.assertEqual(self.cf.token['expires_in'], 0)

    @mock_token
    def test_prepare_token(self):
        """ Test that token is prepared properly to make api call """
        token = self.cf.prepare_token()
        self.assertEqual(token, '999')

    @mock_token
    def test_token_renewed(self):
        """ Check that token is renewed """
        old_token_time = self.cf.token['time_stamp']
        self.cf.prepare_token()
        new_token_time = self.cf.token['time_stamp']
        self.assertNotEqual(old_token_time, new_token_time)

    @mock_token
    @mock_quotas_request
    def test_make_request(self):
        """ Check that calling api works properly """
        get_req = self.cf.make_request('http://api.test.com')
        self.assertEqual(len(get_req.json()['resources']), 2)

    @mock_token
    @mock_quotas_request
    def test_get_quotas(self):
        """ Test that quotas are obtained properly """
        quotas = list(self.cf.get_quotas())
        self.assertEqual(len(quotas), 2)

    @mock_token
    @mock_quotas_request
    def test_yield_request(self):
        """ Test that yield_request produces a generator that iterates through
        pages """
        quotas = self.cf.yield_request('v2/quota_definitions/quota_guid')
        self.assertTrue(isinstance(quotas, types.GeneratorType))
        self.assertEqual(len(list(quotas)[0]['resources']), 2)

    @mock_token
    @mock_orgs_request
    def test_get_orgs(self):
        """ Test that function produces a generator that iterates through
        orgs """
        orgs = list(self.cf.get_orgs())
        self.assertEqual(len(orgs[0]['resources']), 2)


class QuotaModelsTest(TestCase):
    """ Test Database """

    def create_app(self):
        app.config['LIVESERVER_PORT'] = 8943
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_quota(self):
        """ Check that quota is created properly """
        # Create quota
        new_quota = Quota(guid='test_guid', name='test_name', url='test_url')
        new_quota.created_at = datetime.date(2014, 1, 1)
        new_quota.updated_at = datetime.date(2015, 1, 1)
        db.session.add(new_quota)
        db.session.commit()
        # Find quota in database
        quota = Quota.query.filter_by(guid='test_guid').first()
        self.assertEqual(quota.name, 'test_name')
        self.assertEqual(quota.url, 'test_url')
        self.assertEqual(quota.created_at, datetime.datetime(2014, 1, 1))
        self.assertEqual(quota.updated_at, datetime.datetime(2015, 1, 1))

    def test_primary_key_constraint(self):
        """ Test that only one instance of a quota can be created """
        # Adding two instances of the same Quota with same dates
        new_quota = Quota(guid='test_guid', name='test_name', url='test_url')
        db.session.add(new_quota)
        new_quota = Quota(guid='test_guid', name='test_name', url='test_url')
        db.session.merge(new_quota)
        db.session.commit()
        # Getting data from quota
        quotas = Quota.query.filter_by(guid='test_guid').all()
        self.assertEqual(len(quotas), 1)


class DatabaseForeignKeyTest(TestCase):
    """ Test Database """

    def create_app(self):
        app.config['LIVESERVER_PORT'] = 8943
        return app

    def setUp(self):
        db.create_all()
        self.quota = Quota(guid='guid', name='test_name', url='test_url')
        db.session.add(self.quota)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_quota_data(self):
        """ Check that quota data can be added """
        # Adding QuotaData
        quota_data = QuotaData(self.quota, datetime.date(2014, 1, 1))
        quota_data.memory_limit = 1
        quota_data.total_routes = 2
        quota_data.total_services = 3
        self.quota.data.append(quota_data)
        db.session.commit()
        # Retrieve QuotaData
        quota = Quota.query.filter_by(guid='guid').first()
        self.assertEqual(quota.name, 'test_name')
        self.assertEqual(len(list(quota.data)), 1)
        self.assertEqual(quota.data[0].memory_limit, 1)
        self.assertEqual(quota.data[0].total_routes, 2)
        self.assertEqual(quota.data[0].total_services, 3)
        self.assertEqual(quota.data[0].date_collected.year, 2014)

    def test_primary_key_constraints_for_quotadata(self):
        """ Check that the PrimaryKeyConstraints work for QuotaData """
        failed = False
        quota_data = QuotaData(self.quota)
        quota_data_2 = QuotaData(self.quota)
        self.quota.data.append(quota_data)
        self.quota.data.append(quota_data_2)
        try:
            db.session.commit()
        except:
            failed = True
        self.assertTrue(failed)

    def test_quota_data_one_to_many(self):
        """ Check that the relationship between Quota and QuotaData is
        one to many """
        # Creating Quota and 2 instances QuotaData with diff. dates
        quota_data = QuotaData(self.quota)
        quota_data.date_collected = datetime.date(2015, 1, 1)
        quota_data_2 = QuotaData(self.quota)
        self.quota.data.append(quota_data)
        self.quota.data.append(quota_data_2)
        db.session.commit()
        # Retrieve QuotaData
        quota = Quota.query.filter_by(guid='guid').first()
        self.assertEqual(len(list(quota.data)), 2)


class APITest(TestCase):
    """ Test API """

    def create_app(self):
        app.config['LIVESERVER_PORT'] = 8943
        return app

    def setUp(self):
        db.create_all()
        quota = Quota(guid='test_guid', name='test_name', url='test_url')
        db.session.add(quota)
        quota2 = QuotaResource(
            guid='test_guid_2', name='test_name_2', url='test_url_2')
        db.session.add(quota2)
        db.session.commit()
        quota_data = QuotaData(quota, datetime.date(2013, 1, 1))
        quota_data.memory_limit = 2000
        quota.data.append(quota_data)
        quota_data = QuotaData(quota, datetime.date(2014, 1, 1))
        quota_data.memory_limit = 1000
        quota.data.append(quota_data)
        quota_data = QuotaData(quota, datetime.date(2015, 1, 1))
        quota_data.memory_limit = 1000
        quota.data.append(quota_data)
        db.session.commit()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_details(self):
        """ Check that the details function returns dict of the quota """
        quota = QuotaResource.query.filter_by(guid='test_guid').first()

        quota_dict = quota.details()
        self.assertEqual(
            sorted(list(quota_dict.keys())),
            ['created_at', 'guid', 'name', 'updated_at'])

    def test_list_one_details(self):
        """ Check that list one function returns dict of one quota """
        one_quota = QuotaResource.list_one_details(guid='test_guid')
        self.assertEqual(one_quota['guid'], 'test_guid')
        self.assertEqual(one_quota['name'], 'test_name')

    def test_list_one_aggregate(self):
        """ Check that the aggregator functionp produces all data include
        cost """
        one_quota = QuotaResource.list_one_aggregate(guid='test_guid')
        self.assertEqual(one_quota['guid'], 'test_guid')
        self.assertEqual(one_quota['cost'], 13.2)

    def test_list_all(self):
        """ Check that list all function returns dict of multiple quotas """
        quotas = QuotaResource.list_all()
        self.assertEqual(len(quotas), 2)
        self.assertEqual(quotas[0]['guid'], 'test_guid')
        self.assertEqual(quotas[1]['guid'], 'test_guid_2')

    def test_get_mem_single_cost(self):
        """ Check that the cost function works with multiple days
        with single mem limit """
        sample_data = [[1875, 14]]
        cost = QuotaResource.get_mem_cost(sample_data)
        self.assertEqual(cost, 86.625)

    def test_get_mem_cost_multipe_mem_types(self):
        """ Check that the cost function works with multiple days
        with multiple mem limits """
        sample_data = [[1875, 14], [2000, 15]]
        cost = QuotaResource.get_mem_cost(sample_data)
        self.assertEqual(cost, 185.625)

    def test_prepare_memory_data(self):
        """ Check that memory data is prepared into more descriptive format """
        sample_data = [[1875, 14], [2000, 15]]
        memory_data = QuotaResource.prepare_memory_data(sample_data)
        self.assertEqual([
            {'size': 1875, 'days': 14}, {'size': 2000, 'days': 15}
        ], memory_data)

    def test_prepare_csv_row(self):
        """ Check that function returns one row of prepared csv data """
        sample_row = {
            'name': 'test',
            'guid': 'id2',
            'cost': 4,
            'created_at': datetime.datetime(2014, 4, 4)
        }
        row = QuotaResource.prepare_csv_row(sample_row)
        self.assertEqual(['test', 'id2', '4', '2014-04-04 00:00:00'], row)

    def test_generate_cvs(self):
        """ Check that function returns a csv generator """
        csv = QuotaResource.generate_cvs().split('\r\n')
        self.assertEqual(
            'quota_name,quota_guid,quota_cost,quota_created_date',
            csv[0])
        self.assertEqual('test_name,test_guid,13.2,None', csv[1])
        self.assertEqual('test_name_2,test_guid_2,0,None', csv[2])

    def test_quota_list_one_with_data_details(self):
        """ Check that list one returns a list of data details within the
        designated time period """

        # Check that correct quota data is returned by date strings
        one_quota = QuotaResource.list_one_details(
            guid='test_guid', start_date='2013-12-31', end_date='2014-07-02')
        self.assertEqual(len(one_quota['memory']), 1)

        # Check that correct quota data is returned by datetime.dates
        one_quota = QuotaResource.list_one_details(
            guid='test_guid',
            start_date=datetime.date(2013, 12, 31),
            end_date=datetime.date(2014, 1, 2))
        self.assertEqual(len(one_quota['memory']), 1)

    def test_quotadata_details(self):
        """ Check that details function returns dict for a specific
        quotadata object """
        data = QuotaDataResource.query.filter_by(quota='test_guid').first()
        self.assertTrue('memory_limit' in data.details().keys())

    def test_quotadata_aggregate(self):
        """ Check that the aggregate function return the number of days a
        Quota has been active
        """
        # Aggregate
        data = QuotaDataResource.aggregate(quota_guid='test_guid')
        # Data looks like this [(1000, 2), (2000, 1)]
        # Addition test allows the test to work with postgres and sqlite
        self.assertEqual(data[0][1] + data[1][1], 3)

        # Aggregate with dates
        data = QuotaDataResource.aggregate(
            quota_guid='test_guid',
            start_date='2013-01-01',
            end_date='2014-07-01')
        # Data looks like this [(1000, 1), (2000, 1)]
        # Addition test allows the test to work with postgres and sqlite
        self.assertEqual(data[0][1] + data[1][1], 2)

    def test_foreign_key_preparer(self):
        """ Verify that function prepares a details list for a given
        foreign key """
        quota = QuotaResource.query.filter_by(guid='test_guid').first()
        # Check function with no date range
        data = quota.foreign_key_preparer(QuotaDataResource)
        self.assertEqual(len(data), 3)
        # Check function with date range
        data = quota.foreign_key_preparer(
            QuotaDataResource, start_date='2013-12-31', end_date='2014-1-2')
        self.assertEqual(len(data), 1)


# Set header for auth
valid_header = Headers()
auth = '{0}:{1}'.format(Config.USERNAME, Config.PASSWORD).encode('ascii')
valid_header.add('Authorization', b'Basic ' + base64.b64encode(auth))


class QuotaAppTest(TestCase):
    """ Test Database """

    def create_app(self):
        app.config['LIVESERVER_PORT'] = 8943
        return app

    @classmethod
    def setUpClass(cls):
        db.create_all()
        quota_1 = Quota(guid='guid', name='test_name', url='test_url')
        db.session.add(quota_1)
        quota_2 = Quota(guid='guid_2', name='test_name_2', url='test_url_2')
        db.session.add(quota_2)
        quota_data = QuotaData(quota_1)
        quota_data.date_collected = datetime.date(2014, 1, 1)
        quota_data.memory_limit = 1000
        quota_data_2 = QuotaData(quota_1)
        quota_data_2.memory_limit = 1000
        quota_1.data.append(quota_data)
        quota_1.data.append(quota_data_2)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()

    def test_main_page_locked(self):
        """ Check if main page is locked """
        response = self.client.get("/")
        self.assert_401(response)
        self.assertTrue('WWW-Authenticate' in response.headers)
        self.assertTrue('Basic' in response.headers['WWW-Authenticate'])

    def test_api_page_locked(self):
        """ Check if api endpoints are locked """
        response = self.client.get("/api/quotas/")
        self.assert_401(response)
        response = self.client.get("/api/quotas/guid/")
        self.assert_401(response)

    def test_admin_page_rejects_bad_password(self):
        """ Check that incorrect password won't allow access """
        h = Headers()
        auth = '{0}:foo'.format(Config.USERNAME).encode('ascii')
        h.add('Authorization', b'Basic ' + base64.b64encode(auth))
        rv = Client.open(self.client, path='/', headers=h)
        self.assert_401(rv)

    def test_admin_page_rejects_bad_username(self):
        """ Check that incorrect username won't allow access """
        h = Headers()
        auth = 'foo:{0}'.format(Config.PASSWORD).encode('ascii')
        h.add('Authorization', b'Basic ' + base64.b64encode(auth))
        rv = Client.open(self.client, path='/', headers=h)
        self.assert_401(rv)

    def test_admin_page_allows_valid_login(self):
        """ Check that correct username and password will allow access """
        h = Headers()
        auth = '{0}:{1}'.format(
            Config.USERNAME, Config.PASSWORD).encode('ascii')
        h.add('Authorization', b'Basic ' + base64.b64encode(auth))
        rv = Client.open(self.client, path='/', headers=h)
        self.assert_200(rv)

    def test_main_page(self):
        """ Test the main page """
        response = Client.open(self.client, path='/', headers=valid_header)
        self.assertEqual(response.status_code, 200)

    def test_api_quotas_page(self):
        """ Test the quota list page """
        response = Client.open(
            self.client, path="/api/quotas/", headers=valid_header)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['Quotas']), 2)

    def test_api_quota_detail_page(self):
        """ Test the quota details page """
        response = Client.open(
            self.client, path="/api/quotas/guid/", headers=valid_header)
        self.assertEqual(response.status_code, 200)
        # Check if quota was rendered
        self.assertTrue('guid' in response.json.keys())
        # Check if quota data was rendered
        self.assertEqual(len(response.json['memory']), 1)

    def test_api_quota_detail_page_no_data(self):
        """ Test the quota details page when there is no data """
        response = Client.open(
            self.client, path="/api/quota/wrongguid/", headers=valid_header)
        self.assertEqual(response.status_code, 404)

    def test_api_quota_detail_dates(self):
        """ Test the quota details date range page functions """
        response = Client.open(
            self.client,
            path="/api/quotas/guid/?since=2013-12-31&until=2014-1-1",
            headers=valid_header)
        self.assertEqual(response.status_code, 200)
        # Check if quota data was rendered within date range
        self.assertEqual(len(response.json['memory']), 1)

    def test_api_quota_detail_page_one_date(self):
        """ Test the quota details page with only the since parameter """
        response = Client.open(
            self.client,
            path="/api/quotas/guid/?since=2013-12-31",
            headers=valid_header)
        self.assertEqual(response.status_code, 200)
        # Check if quota was rendered
        self.assertTrue('guid' in response.json.keys())
        # Check if quota data was rendered
        self.assertEqual(len(response.json['memory']), 1)

    def test_api_quota_detail_dates_no_data(self):
        """ Test the quota details page when there are date but no data """
        response = Client.open(
            self.client,
            path="/api/quota/wrongguid/2013-12-31/2014-1-1/",
            headers=valid_header)
        self.assertEqual(response.status_code, 404)

    def test_api_quotas_list_page(self):
        """ Test the quotas list page """
        response = Client.open(
            self.client, path="/api/quotas/", headers=valid_header)
        self.assertEqual(response.status_code, 200)
        data = response.json['Quotas']
        # Check if all quotas present
        self.assertEqual(len(data), 2)
        # Check if quota data contains data details
        self.assertEqual(len(data[0]['memory']), 1)

    def test_api_quotas_list_dates(self):
        """ Test the quotas list page with dates """
        response = Client.open(
            self.client,
            path="/api/quotas/?since=2012-12-31&until=2013-1-1",
            headers=valid_header)
        self.assertEqual(response.status_code, 200)
        data = response.json['Quotas']
        # Check if all quotas present
        self.assertEqual(len(data), 2)
        # Check if quota data contains memory data only when inbetween dates
        self.assertEqual(len(data[0]['memory']), 0)

    def test_api_quotas_list_page_one_date(self):
        """ Test the quotas list page when only since date is given """
        response = Client.open(
            self.client,
            path="/api/quotas/?since=2012-12-31",
            headers=valid_header)
        self.assertEqual(response.status_code, 200)
        data = response.json['Quotas']
        # Check if all quotas present
        self.assertEqual(len(data), 2)
        # Check if quota data contains data details
        self.assertEqual(len(data[0]['memory']), 1)


class LoadingTest(TestCase):
    """ Test Database """

    def create_app(self):
        app.config['LIVESERVER_PORT'] = 8943
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_datetime(self):
        """ Test that date string coverted to date """
        date = '2015-01-01T01:01:01Z'
        new_data = scripts.get_datetime(date)
        self.assertEqual(new_data, datetime.date(2015, 1, 1))

    def test_update_quota(self):
        """ Test that function inserts quota into database """
        scripts.update_quota(mock_quota)
        quota = Quota.query.filter_by(guid='test_quota').first()
        self.assertEqual(quota.name, 'test_quota_name')

    def test_name_change(self):
        """ Test that function changes name but keeps guid in case of a name
        change """
        scripts.update_quota(mock_quota)
        quota = Quota.query.filter_by(guid='test_quota').first()
        self.assertEqual(quota.name, 'test_quota_name')
        self.assertEqual(quota.data[0].memory_limit, 1875)

        mock_quota_name = copy.deepcopy(mock_quota)
        mock_quota_name['entity']['name'] = "new_name"
        scripts.update_quota(mock_quota_name)
        quota = Quota.query.filter_by(guid='test_quota').first()
        self.assertEqual(quota.name, 'new_name')
        self.assertEqual(quota.data[0].memory_limit, 1875)

    def test_update_quota_data(self):
        """ Test that function inserts quota data into database """
        # Add quota
        quota = Quota(guid='guid', name='test_name', url='test_url')
        db.session.add(quota)
        # Add quota data
        scripts.update_quota_data(
            quota_model=quota, entity_data=mock_quota['entity'])
        db.session.commit()
        # Check if data was added
        quota = Quota.query.filter_by(guid='guid').first()
        self.assertEqual(quota.data[0].memory_limit, 1875)

    def test_get_or_create_create(self):
        """ Test that get_or_create function creates a new object """
        quota = Quota.query.filter_by(guid='test_guid').all()
        self.assertEqual(len(quota), 0)
        create_quota, created = scripts.get_or_create(
            Quota, guid='test_guid', name='test_name', url='test_url')
        self.assertTrue(created)
        found = Quota.query.filter_by(guid='test_guid').all()
        self.assertEqual(len(found), 1)

    def test_get_or_create_get(self):
        """ Test that get_or_create function gets an old object """
        # Create and add a quota
        quota = Quota(guid='test_guid', name='test_name', url='test_url')
        db.session.add(quota)
        db.session.commit()
        # Try to get the same quota
        ret_quota, created = scripts.get_or_create(
            Quota, guid='test_guid', name='test_name', url='test_url')
        self.assertEqual(ret_quota.guid, 'test_guid')
        self.assertFalse(created)
        # Check if there are duplicates
        found = Quota.query.filter_by(guid='test_guid').all()
        self.assertEqual(len(found), 1)


if __name__ == "__main__":
    unittest.main()
