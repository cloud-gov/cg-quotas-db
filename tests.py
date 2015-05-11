import copy
import datetime
import requests
import unittest

from flask.ext.testing import TestCase
from unittest import mock

from cloudfoundry import CloudFoundry
from quotas import app, db
from models import Org
import scripts

mock_org = {
    'metadata': {
        'created_at': '2015-01-01T01:01:01Z',
        'guid': 'test_org',
        'total_routes': 5,
        'updated_at': '2015-01-01T01:01:01Z',
        'url': '/v2/quota_definitions/test'
    },
    'entity': {
        'name': 'test_org_name',
        'memory_limit': 1875,
        'total_routes': 5,
        'total_services': 1,
    }
}
mock_org_2 = copy.deepcopy(mock_org)
mock_org_2['metadata']['guid'] = 'test_org_2'


class MockTokenReq:
    """ Returns a mock token in json form """
    def json():
        return {'access_token': '999', 'expires_in': 0}


class MockGetReq:
    """ Returns a mock token in json form """
    def json():
        return {'resources': [mock_org, mock_org_2]}


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
    def test_init(self):
        """ Test that CloudFoundry object initializes properly """

        cf = CloudFoundry(
            url='api.test.com',
            username='mockusername@mock.com',
            password='******')
        self.assertEqual(cf.url, 'api.test.com')
        self.assertEqual(cf.username, 'mockusername@mock.com')
        self.assertEqual(cf.password, '******')
        self.assertEqual(cf.token['access_token'], '999')
        self.assertEqual(cf.token['expires_in'], 0)

    @mock_token
    def test_prepare_token(self):
        """ Test that token is prepared properly to make api call """

        # Check that token is prepared
        cf = CloudFoundry(
            url='api.test.com',
            username='mockusername@mock.com',
            password='******')
        token = cf.prepare_token()
        self.assertEqual(token, '999')

        # Check that token is renewed
        old_token_time = cf.token['time_stamp']
        token = cf.prepare_token()
        new_token_time = cf.token['time_stamp']
        self.assertNotEqual(old_token_time, new_token_time)

    @mock_token
    @mock_get_request
    def test_mock_get_request(self):
        """ Check that calling api works properly """
        cf = CloudFoundry(
            url='api.test.com',
            username='mockusername@mock.com',
            password='******')
        get_req = cf.make_request('http://api.test.com')
        self.assertEqual(len(get_req.json()['resources']), 2)

    @mock_token
    @mock_get_request
    def test_get_quotas(self):
        """ Test that quotas are obtained properly """
        cf = CloudFoundry(
            url='api.test.com',
            username='mockusername@mock.com',
            password='******')
        quotas = cf.get_quotas()
        self.assertEqual(len(quotas['resources']), 2)

    @mock_token
    @mock_get_request
    def test_get_quota_details(self):
        """ Test that quota details for a specific org are obtained """
        cf = CloudFoundry(
            url='api.test.com',
            username='mockusername@mock.com',
            password='******')
        quotas = cf.get_quota_details('v2/api/org2')
        self.assertEqual(len(quotas['resources']), 2)


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

    def test_create_org(self):
        """ Check that org is created properly """
        new_org = Org(guid='test_guid', name='test_name', url='test_url')
        new_org.memory_limit = 100
        new_org.total_routes = 1000
        new_org.total_services = 1
        new_org.created_at = datetime.datetime(2014, 1, 1)
        new_org.updated_at = datetime.datetime(2015, 1, 1)

        db.session.add(new_org)
        db.session.commit()
        org = Org.query.filter_by(guid='test_guid').first()
        self.assertEqual(org.name, 'test_name')
        self.assertEqual(org.url, 'test_url')
        self.assertEqual(org.date_collected.day, datetime.date.today().day)
        self.assertEqual(org.memory_limit, 100)
        self.assertEqual(org.total_routes, 1000)
        self.assertEqual(org.total_services, 1)
        self.assertEqual(org.created_at.day, 1)
        self.assertEqual(org.updated_at.day, 1)

    def test_primary_key_constraint(self):
        """ Test that unique constraint is a composite of guid and date """
        # Adding two instances of the same Org with different dates
        new_org = Org(guid='test_guid', name='test_name', url='test_url')
        new_org.date_collected = datetime.datetime(2014, 1, 1)
        db.session.add(new_org)
        new_org = Org(guid='test_guid', name='test_name', url='test_url')
        db.session.merge(new_org)
        db.session.commit()
        # Getting data from org
        orgs = Org.query.filter_by(guid='test_guid').all()
        self.assertEqual(len(orgs), 2)

    def test_primary_key_constraint_single(self):
        """ Test that unique constraint is a composite of guid and date """
        # Adding two instances of the same Org with same dates
        new_org = Org(guid='test_guid', name='test_name', url='test_url')
        db.session.add(new_org)
        new_org = Org(guid='test_guid', name='test_name', url='test_url')
        db.session.merge(new_org)
        db.session.commit()
        # Getting data from org
        orgs = Org.query.filter_by(guid='test_guid').all()
        self.assertEqual(len(orgs), 1)

    def test_display(self):
        """ Check that the display function returns dict """
        new_org = Org(guid='test_guid', name='test_name', url='test_url')
        db.session.add(new_org)
        db.session.commit()
        org_dict = new_org.display()
        self.assertEqual(org_dict['guid'], 'test_guid')
        self.assertEqual(org_dict['name'], 'test_name')

    def test_list_one(self):
        """ Check that list one function returns dict of one org """
        new_org = Org(guid='test_guid', name='test_name', url='test_url')
        db.session.add(new_org)
        db.session.commit()
        one_org = Org.list_one(guid='test_guid')[0]
        self.assertEqual(one_org['guid'], 'test_guid')
        self.assertEqual(one_org['name'], 'test_name')

    def test_list_all(self):
        """ Check that list all function returns dict of multiple orgs """
        new_org = Org(guid='test_guid', name='test_name', url='test_url')
        db.session.add(new_org)
        new_org = Org(guid='test_guid_2', name='test_name_2', url='test_url_2')
        db.session.add(new_org)
        db.session.commit()
        orgs = Org.list_all()
        self.assertEqual(len(orgs), 2)
        self.assertEqual(orgs[0]['guid'], 'test_guid')
        self.assertEqual(orgs[1]['guid'], 'test_guid_2')


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
        new_org = Org(guid='test_guid', name='test_name', url='test_url')
        db.session.add(new_org)
        new_org = Org(guid='test_guid_2', name='test_name_2', url='test_url_2')
        db.session.add(new_org)
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

    def test_api_orgs_page(self):
        """ Test the orgs list page """
        response = self.client.get("/api/orgs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['Orgs']), 2)

    def test_api_org_detail_page(self):
        """ Test the org details page """
        response = self.client.get("/api/org/test_guid")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['Org']), 1)


class LoadingTest(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()

    def test_get_datetime(self):
        """ Test that date string coverted to date """
        date = '2015-01-01T01:01:01Z'
        new_data = scripts.get_datetime(date)
        self.assertEqual(new_data, datetime.date(2015, 1, 1))

    def test_update_quota(self):
        """ Test that function inserts quota into database """
        scripts.update_quota(mock_org)
        org = Org.query.filter_by(guid='test_org').first()
        self.assertEqual(org.name, 'test_org_name')
        self.assertEqual(org.memory_limit, 1875)

    @mock_token
    @mock_get_request
    def test_load_quotas(self):
        """ Test that function loads multiple quotas """
        scripts.load_quotas()
        orgs = Org.query.order_by().all()
        self.assertEqual(len(orgs), 2)

if __name__ == "__main__":
    unittest.main()
