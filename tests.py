# Extral Imports
from unittest import mock
from flask.ext.testing import TestCase
import copy
import datetime
import requests
import types
import unittest

# App imports
from cloudfoundry import CloudFoundry
from quotas import app, db
from models import Quota, QuotaData
import scripts

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
        'total_services': 1,
    }
}
mock_quota_2 = copy.deepcopy(mock_quota)
mock_quota_2['metadata']['guid'] = 'test_quota_2'


class MockTokenReq:
    """ Returns a mock token in json form """
    def json():
        return {'access_token': '999', 'expires_in': 0}


class MockGetReq:
    """ Returns a mock token in json form """
    def json():
        return {
            'next_url': None,
            'resources': [mock_quota, mock_quota_2]
        }


def mock_token(func):
    """ Patches post request and return a mock token """
    def _mock_token(*args, **kwargs):
        with mock.patch.object(requests, 'post', return_value=MockTokenReq):
            return func(*args, **kwargs)
    return _mock_token


def mock_get_request(func):
    """ Patches get request and return mock quota definitions """
    def _mock_get(*args, **kwargs):
        with mock.patch.object(requests, 'get', return_value=MockGetReq):
            return func(*args, **kwargs)
    return _mock_get


class CloudFoundryTest(unittest.TestCase):
    """ Test CloudFoundry client """

    @mock_token
    def setUp(self):
        self.cf = CloudFoundry(
            url='api.test.com',
            username='mockusername@mock.com',
            password='******')

    @mock_token
    def test_init(self):
        """ Test that CloudFoundry object initializes properly """

        self.assertEqual(self.cf.url, 'api.test.com')
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
    @mock_get_request
    def test_make_request(self):
        """ Check that calling api works properly """
        get_req = self.cf.make_request('http://api.test.com')
        self.assertEqual(len(get_req.json()['resources']), 2)

    @mock_token
    @mock_get_request
    def test_get_quotas(self):
        """ Test that quotas are obtained properly """
        quotas = list(self.cf.get_quotas())
        self.assertEqual(len(quotas[0]['resources']), 2)

    @mock_token
    @mock_get_request
    def test_yield_request(self):
        """ Test that yield_request produces a generator that iterates through
        pages """
        quotas = self.cf.yield_request('v2/quota_definitions/quota_guid')
        self.assertTrue(isinstance(quotas, types.GeneratorType))
        self.assertEqual(len(list(quotas)[0]['resources']), 2)


class DatabaseTest(TestCase):
    """ Test Database """

    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def create_app(self):
        app.config['TESTING'] = True
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
        new_quota.created_at = datetime.datetime(2014, 1, 1)
        new_quota.updated_at = datetime.datetime(2015, 1, 1)
        db.session.add(new_quota)
        db.session.commit()
        # Find quota in database
        quota = Quota.query.filter_by(guid='test_guid').first()
        self.assertEqual(quota.name, 'test_name')
        self.assertEqual(quota.url, 'test_url')
        self.assertEqual(quota.created_at.day, 1)
        self.assertEqual(quota.updated_at.day, 1)

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

    def test_details(self):
        """ Check that the details function returns dict of the quota """
        new_quota = Quota(guid='test_guid', name='test_name', url='test_url')
        db.session.add(new_quota)
        db.session.commit()
        quota_dict = new_quota.details()
        self.assertEqual(
            sorted(list(quota_dict.keys())),
            ['created_at', 'guid', 'name', 'updated_at', 'url'])

    def test_list_one(self):
        """ Check that list one function returns dict of one quota """
        new_quota = Quota(guid='test_guid', name='test_name', url='test_url')
        db.session.add(new_quota)
        db.session.commit()
        one_quota = Quota.list_one(guid='test_guid')
        self.assertEqual(one_quota['guid'], 'test_guid')
        self.assertEqual(one_quota['name'], 'test_name')

    def test_list_all(self):
        """ Check that list all function returns dict of multiple quotas """
        new_quota = Quota(guid='guid', name='test_name', url='test_url')
        db.session.add(new_quota)
        new_quota = Quota(guid='guid2', name='test_name_2', url='test_url_2')
        db.session.add(new_quota)
        db.session.commit()
        quotas = Quota.list_all()
        self.assertEqual(len(quotas), 2)
        self.assertEqual(quotas[0]['guid'], 'guid')
        self.assertEqual(quotas[1]['guid'], 'guid2')

    def test_quota_data(self):
        """ Check that quota data can be added """
        # Creating Quota and QuotaData
        new_quota = Quota(guid='guid', name='test_name', url='test_url')
        db.session.add(new_quota)
        quota_data = QuotaData(new_quota)
        quota_data.memory_limit = 1
        quota_data.total_routes = 2
        quota_data.total_services = 3
        new_quota.data.append(quota_data)
        db.session.commit()
        # Retrieve QuotaData
        quota = Quota.query.filter_by(guid='guid').first()
        self.assertEqual(quota.name, 'test_name')
        self.assertEqual(len(list(quota.data)), 1)
        self.assertEqual(quota.data[0].memory_limit, 1)
        self.assertEqual(quota.data[0].total_routes, 2)
        self.assertEqual(quota.data[0].total_services, 3)

    def test_primary_key_constraints_for_quotadata(self):
        """ Check that the PrimaryKeyConstraints work for QuotaData """
        failed = False
        new_quota = Quota(guid='guid', name='test_name', url='test_url')
        db.session.add(new_quota)
        quota_data = QuotaData(new_quota)
        quota_data_2 = QuotaData(new_quota)
        new_quota.data.append(quota_data)
        new_quota.data.append(quota_data_2)
        try:
            db.session.commit()
        except:
            failed = True
        self.assertTrue(failed)

    def test_quota_data_one_to_many(self):
        """ Check that the relationship between Quota and QuotaData is
        one to many """
        # Creating Quota and 2 instances QuotaData with diff. dates
        new_quota = Quota(guid='guid', name='test_name', url='test_url')
        db.session.add(new_quota)
        quota_data = QuotaData(new_quota)
        quota_data.date_collected = datetime.date(2015, 1, 1)
        quota_data_2 = QuotaData(new_quota)
        new_quota.data.append(quota_data)
        new_quota.data.append(quota_data_2)
        db.session.commit()
        # Retrieve QuotaData
        quota = Quota.query.filter_by(guid='guid').first()
        self.assertEqual(len(list(quota.data)), 2)


class QuotaAppTest(TestCase):
    """ Test Database """

    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def create_app(self):
        app.config['TESTING'] = True
        app.config['LIVESERVER_PORT'] = 8943
        return app

    @classmethod
    def setUpClass(cls):
        db.create_all()
        new_quota = Quota(guid='guid', name='test_name', url='test_url')
        db.session.add(new_quota)
        new_quota = Quota(guid='guid_2', name='test_name_2', url='test_url_2')
        db.session.add(new_quota)
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()

    def test_main_page(self):
        """ Test the main page """
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_api_page(self):
        """ Test the main api page """
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)

    def test_api_quotas_page(self):
        """ Test the quota list page """
        response = self.client.get("/api/quotas")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['Quotas']), 2)

    def test_api_quota_detail_page(self):
        """ Test the quota details page """
        response = self.client.get("/api/quotas/guid")
        self.assertEqual(response.status_code, 200)
        self.assertTrue('guid' in response.json.keys())


class LoadingTest(TestCase):
    """ Test Database """

    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def create_app(self):
        app.config['TESTING'] = True
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

    @mock_token
    @mock_get_request
    def test_load_quotas(self):
        """ Test that function loads multiple quotas """
        scripts.load_quotas()
        quotas = Quota.query.all()
        self.assertEqual(len(quotas), 2)

if __name__ == "__main__":
    unittest.main()
