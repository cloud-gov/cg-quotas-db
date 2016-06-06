import time
import requests


class CloudFoundry:

    """ Script for connecting to a Clound Foundry url and requesting data """

    def __init__(self, api_url, uaa_url, username, password):

        self.api_url = api_url
        self.uaa_url = uaa_url
        self.username = username
        self.password = password
        self.request_token()

    def request_token(self):
        """ Request a token from service """
        token_url = '%s/oauth/token' % self.uaa_url
        headers = {
            'accept': 'application/json',
            'authorization': 'Basic Y2Y6'
        }
        params = {
            'username': self.username,
            'password': self.password,
            'grant_type': 'password'
        }
        r = requests.post(url=token_url, headers=headers, params=params)
        self.token = r.json()
        self.token['time_stamp'] = time.time()

    def prepare_token(self):
        """ Check if token is expired and open access token """
        time_elapsed = time.time() - self.token['time_stamp']
        if time_elapsed > self.token['expires_in']:
            self.request_token()
        return self.token['access_token']

    def make_request(self, endpoint):
        """ Make request to specific endpoint """
        token = self.prepare_token()
        url = '{0}{1}'.format(self.api_url, endpoint)
        headers = {'authorization': 'bearer ' + token}
        req = requests.get(url=url, headers=headers)
        return req

    def yield_request(self, endpoint):
        """ Yield all of the request pages """
        while endpoint:
            req = self.make_request(endpoint=endpoint).json()
            endpoint = req.get('next_url')
            yield req

    def get_quotas(self):
        """ Get quota definitions """
        quotas_gen = self.yield_request(endpoint='/v2/quota_definitions')
        for quota_bundle in quotas_gen:
            if 'resources' in quota_bundle:
                for quota in quota_bundle['resources']:
                    yield quota

    def get_orgs(self):
        """ Get org data """
        req_iterator = self.yield_request(endpoint='/v2/organizations')
        for req in req_iterator:
            yield req
