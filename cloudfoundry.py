import time
import requests


class CloudFoundry:

    """ Script for connecting to a Clound Foundry url and requesting data """

    def __init__(self, url, username, password):

        self.url = url
        self.username = username
        self.password = password
        self.request_token()

    def request_token(self):
        """ Request a token from service """
        token_url = 'https://uaa.%s/oauth/token' % self.url
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
        url = 'https://api.{0}/{1}'.format(self.url, endpoint)
        headers = {'authorization': 'bearer ' + token}
        r = requests.get(url=url, headers=headers)
        return r

    def get_quotas(self):
        """ Get quota definitions """
        r = self.make_request(endpoint='v2/quota_definitions')
        return r.json()

    def get_quota_details(self, endpoint):
        r = self.make_request(endpoint=endpoint)
        return r.json()
