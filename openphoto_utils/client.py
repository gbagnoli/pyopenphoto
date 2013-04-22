
from functools import partial
import requests
import requests_oauthlib

class OpenphotoHttpClient(object):

    def __init__(self, config):
        self.config = config
        self.auth = requests_oauthlib.OAuth1(
            config.api.consumer_key,
            config.api.consumer_secret,
            config.api.oauth_token,
            config.api.oauth_secret)
        self.session = requests.Session()
        self.host = self.config.api.host
        self.scheme = "https"

    def url(self, endpoint):
        return "{0}://{1}{2}".format(self.scheme, self.host, endpoint)

    def __getattr__(self, attr):
        if attr in ("get", "post", "put", "delete", "patch", "head"):
            return partial(self.request, attr)

        raise AttributeError(attr)

    def request(self, method, endpoint, **kwargs):
        kwargs['auth'] = self.auth
        return self.session.request(method, self.url(endpoint), **kwargs)

