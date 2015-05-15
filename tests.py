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
from models import Quota, QuotaData, Service
import scripts
import vcr

# Flipp app settings
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
        'total_services': 1,
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
                "quota_definition_url": "/v2/quota_definitions/f7963421-c06e-4847-9913-bcd0e6048fa2",
                "spaces_url": "/v2/organizations/f190f9a3-d89f-4684-8ac4-6f76e32c3e05/spaces",
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
        {'guid': 'guid_1', 'name': 'hub-es15-highmem'},
        {'guid': 'guid_2', 'name': 'es'}
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
        self.assertEqual(len(quotas[0]['resources']), 2)

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

    def test_details(self):
        """ Check that the details function returns dict of the quota """
        new_quota = Quota(guid='test_guid', name='test_name', url='test_url')
        db.session.add(new_quota)
        db.session.commit()
        quota_dict = new_quota.details()
        self.assertEqual(
            sorted(list(quota_dict.keys())),
            ['created_at', 'guid', 'name', 'updated_at', 'url'])

    def test_list_one_details(self):
        """ Check that list one function returns dict of one quota """
        new_quota = Quota(guid='test_guid', name='test_name', url='test_url')
        db.session.add(new_quota)
        db.session.commit()
        one_quota = Quota.list_one_details(guid='test_guid')
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


class DatabaseForeignKeyTest(TestCase):
    """ Test Database """

    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def create_app(self):
        app.config['TESTING'] = True
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
        quota_data = QuotaData(self.quota)
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

    def test_quota_list_one_with_data_details(self):
        """ Check that list one returns a list of data details within the
        designated time period """
        # Create new quota with two quotadata
        quota_data = QuotaData(self.quota)
        quota_data.date_collected = datetime.date(2014, 1, 1)
        quota_data_2 = QuotaData(self.quota)
        self.quota.data.append(quota_data)
        self.quota.data.append(quota_data_2)
        db.session.commit()

        # Check that correct quota data is returned by date strings
        one_quota = Quota.list_one_details(
            guid='guid', start_date='2013-12-31', end_date='2014-1-2')
        self.assertEqual(len(one_quota['data']), 1)

        # Check that correct quota data is returned by datetime.dates
        one_quota = Quota.list_one_details(
            guid='guid',
            start_date=datetime.date(2013, 12, 31),
            end_date=datetime.date(2014, 1, 2))
        self.assertEqual(len(one_quota['data']), 1)

    def test_quotadata_details(self):
        """ Check that details function returns dict for a specific
        quotadata object """
        # Create new quota with quotadata
        quota_data = QuotaData(self.quota)
        self.quota.data.append(quota_data)
        db.session.commit()
        # Check details
        quota = Quota.query.filter_by(guid='guid').first()
        self.assertTrue('memory_limit' in quota.data[0].details().keys())

    def test_quotadata_aggregate(self):
        """ Check that the aggregate function return the number of days a
        Quota has been active
        """
        # Add multiple quotas
        quota_data_1 = QuotaData(self.quota)
        quota_data_1.memory_limit = 1000
        quota_data_1.date_collected = datetime.date(2014, 1, 1)
        quota_data_2 = QuotaData(self.quota)
        quota_data_2.memory_limit = 1000
        quota_data_3 = QuotaData(self.quota)
        quota_data_3.memory_limit = 2000
        quota_data_3.date_collected = datetime.date(2013, 1, 1)
        self.quota.data.append(quota_data_1)
        self.quota.data.append(quota_data_2)
        self.quota.data.append(quota_data_3)
        db.session.commit()

        # Aggregate
        data = QuotaData.aggregate(quota_guid=self.quota.guid)
        # Data looks like this [(1000, 2), (2000, 1)]
        # Addition test allows the test to work with postgres and sqlite
        self.assertEqual(data[0][1] + data[1][1], 3)

        # Aggregate with dates
        data = QuotaData.aggregate(
            quota_guid=self.quota.guid,
            start_date='2013-01-01',
            end_date='2015-01-01')
        # Data looks like this [(1000, 1), (2000, 1)]
        # Addition test allows the test to work with postgres and sqlite
        self.assertEqual(data[0][1] + data[1][1], 2)

    def test_service_data(self):
        """ Check that service data can be added """
        # Adding Service data
        service_data = Service(quota=self.quota, guid='sid', name='test')
        self.quota.services.append(service_data)
        db.session.commit()
        # Retrieve Service data
        quota = Quota.query.filter_by(guid='guid').first()
        self.assertEqual(quota.name, 'test_name')
        self.assertEqual(len(quota.services), 1)
        self.assertEqual(quota.services[0].guid, 'sid')

    def test_primary_key_constraints_for_service_data(self):
        """ Check that the PrimaryKeyConstraints work for Service """
        failed = False
        service_1 = Service(quota=self.quota, guid='sid', name='test')
        service_2 = Service(quota=self.quota, guid='sid', name='test')
        self.quota.services.append(service_1)
        self.quota.services.append(service_2)
        try:
            db.session.commit()
        except:
            failed = True
        self.assertTrue(failed)

    def test_service_data_one_to_many(self):
        """ Check that the relationship between Quota and Service is
        one to many """
        # Creating Quota and 2 instances Service with diff. dates
        service_1 = Service(quota=self.quota, guid='sid', name='test')
        service_1.date_collected = datetime.date(2015, 1, 1)
        service_2 = Service(quota=self.quota, guid='sid_2', name='test_2')
        self.quota.services.append(service_1)
        self.quota.services.append(service_2)
        db.session.commit()
        # Retrieve QuotaData
        quota = Quota.query.filter_by(guid='guid').first()
        self.assertEqual(len(list(quota.services)), 2)

    def test_service_list_one_with_data_details(self):
        """ Check that list one returns a list of data details within the
        designated time period """
        # Create new quota with two services
        service_1 = Service(quota=self.quota, guid='sid', name='test')
        service_1.date_collected = datetime.date(2014, 1, 1)
        service_2 = Service(quota=self.quota, guid='sid_2', name='test_2')
        self.quota.services.append(service_1)
        self.quota.services.append(service_2)
        db.session.commit()

        # Check that correct services data is returned by date strings
        one_quota = Quota.list_one_details(
            guid='guid', start_date='2013-12-31', end_date='2014-1-2')
        self.assertEqual(len(one_quota['services']), 1)

        # Check that correct services data is returned by datetime.dates
        one_quota = Quota.list_one_details(
            guid='guid',
            start_date=datetime.date(2013, 12, 31),
            end_date=datetime.date(2014, 1, 2))
        self.assertEqual(len(one_quota['services']), 1)

    def test_service_details(self):
        """ Check that details function returns dict for a specific
        service object """
        # Create new quota with quotadata
        service_1 = Service(quota=self.quota, guid='sid', name='test')
        self.quota.services.append(service_1)
        db.session.commit()
        # Check details
        quota = Quota.query.filter_by(guid='guid').first()
        self.assertTrue('name' in quota.services[0].details().keys())

    def test_foreign_key_preparer(self):
        """ Verify that function prepares a details list for a givin
        foreign key """
        # Create new quota with two quotadata
        quota_data = QuotaData(self.quota)
        quota_data.date_collected = datetime.date(2014, 1, 1)
        quota_data_2 = QuotaData(self.quota)
        self.quota.data.append(quota_data)
        self.quota.data.append(quota_data_2)
        db.session.commit()
        # Check function with no date range
        data = self.quota.foreign_key_preparer(QuotaData)
        self.assertEqual(len(data), 2)
        # Check function with date range
        data = self.quota.foreign_key_preparer(
            QuotaData, start_date='2013-12-31', end_date='2014-1-2')
        self.assertEqual(len(data), 1)

    def test_service_aggregate(self):
        """ Check that the aggregate function return the number of days a
        Service has been active
        """
        # Add multiple quotas
        service_1 = Service(quota=self.quota, guid='pgres', name='postgres')
        service_1.date_collected = datetime.date(2013, 1, 15)
        service_2 = Service(quota=self.quota, guid='pgres', name='postgres')
        service_2.date_collected = datetime.date(2014, 1, 31)
        service_3 = Service(quota=self.quota, guid='elastic', name='es')
        service_3.date_collected = datetime.date(2013, 1, 15)
        self.quota.services.append(service_1)
        self.quota.services.append(service_2)
        self.quota.services.append(service_3)
        db.session.commit()

        # Aggregate
        # Data looks like  [('postgres', 'pgres', 2), ('es', 'elastic', 1)]
        # Addition test allows it to work with both sqlite and postgres
        data = Service.aggregate(quota_guid=self.quota.guid)
        self.assertEqual(data[0][2] + data[1][2], 3)

        # Aggregate with dates
        data = Service.aggregate(
            quota_guid=self.quota.guid,
            start_date='2013-01-01',
            end_date='2013-01-31')
        # Data looks like  [('postgres', 'pgres', 1), ('es', 'elastic', 1)]
        # Addition test allows it to work with both sqlite and postgres
        self.assertEqual(data[0][2] + data[1][2], 2)


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
        quota_1 = Quota(guid='guid', name='test_name', url='test_url')
        db.session.add(quota_1)
        quota_2 = Quota(guid='guid_2', name='test_name_2', url='test_url_2')
        db.session.add(quota_2)
        quota_data = QuotaData(quota_1)
        quota_data.date_collected = datetime.date(2014, 1, 1)
        quota_data_2 = QuotaData(quota_1)
        quota_1.data.append(quota_data)
        quota_1.data.append(quota_data_2)
        service_1 = Service(quota=quota_1, guid='sid', name='test')
        service_1.date_collected = datetime.date(2014, 1, 1)
        service_2 = Service(quota=quota_1, guid='sid_2', name='test_2')
        quota_1.services.append(service_1)
        quota_1.services.append(service_2)
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
        response = self.client.get("/api/quotas/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['Quotas']), 2)

    def test_api_quota_detail_page(self):
        """ Test the quota details page """
        response = self.client.get("/api/quotas/guid/")
        self.assertEqual(response.status_code, 200)
        # Check if quota was rendered
        self.assertTrue('guid' in response.json.keys())
        # Check if quota data was rendered
        self.assertEqual(len(response.json['data']), 1)
        # Check if service data was rendered
        self.assertEqual(len(response.json['services']), 2)

    def test_api_quota_detail_dates(self):
        """ Test the quota details date range page functions """
        response = self.client.get("/api/quotas/guid/2013-12-31/2014-1-1/")
        self.assertEqual(response.status_code, 200)
        # Check if quota data was rendered within date range
        self.assertEqual(len(response.json['data']), 1)
        # Check if service data was rendered
        self.assertEqual(len(response.json['services']), 1)


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

    def test_load_services(self):
        quota = Quota(guid='test_guid', name='test_name', url='test_url')
        db.session.add(quota)
        db.session.commit()
        scripts.load_services(space_summary=mock_space_summary, quota=quota)
        self.assertEqual(len(quota.services), 2)
        self.assertEqual(quota.services[0].guid, 'guid_1')
        self.assertEqual(quota.services[0].name, 'hub-es15-highmem')

    @mock_token
    @vcr.use_cassette('fixtures/load_quotas.yaml')
    def test_process_spaces(self):
        cf_api = CloudFoundry(
            url='18f.gov',
            username='mockusername@mock.com',
            password='*****')
        quota = Quota(guid='test_guid', name='test_name', url='test_url')
        db.session.add(quota)
        db.session.commit()
        url = '/v2/organizations/f190f9a3-d89f-4684-8ac4-6f76e32c3e05/spaces'
        scripts.process_spaces(cf_api=cf_api, spaces_url=url, quota=quota)
        quotas = Quota.query.all()
        self.assertEqual(len(quotas), 1)
        self.assertEqual(len(quotas[0].services), 6)

    @mock_token
    @vcr.use_cassette('fixtures/load_quotas.yaml')
    def test_process_org(self):
        """ Test that process_org function loads quota from org """
        cf_api = CloudFoundry(
            url='18f.gov',
            username='mockusername@mock.com',
            password='*****')
        scripts.process_org(cf_api=cf_api, org=mock_org_data['resources'][0])
        quotas = Quota.query.all()
        self.assertEqual(len(quotas), 1)
        self.assertEqual(len(quotas[0].services), 6)

    @mock_token
    @vcr.use_cassette('fixtures/load_quotas.yaml')
    def test_load_quotas(self):
        """ Test that function loads multiple quotas """
        cf_api = CloudFoundry(
            url='18f.gov',
            username='mockusername@mock.com',
            password='*****')
        scripts.load_quotas(cf_api)
        quotas = Quota.query.all()
        self.assertEqual(len(quotas), 2)
        self.assertEqual(len(quotas[1].data), 1)
        self.assertEqual(
            len(quotas[0].services) + len(quotas[1].services), 6)


if __name__ == "__main__":
    unittest.main()
