#!/usr/bin/env python
import functools
import requests
import requests_oauthlib


class Client(object):

    def __init__(self, host, consumer_key, consumer_secret,
                       oauth_token, oauth_secret, scheme="https"):
        self.auth = requests_oauthlib.OAuth1(
                            consumer_key,
                            consumer_secret,
                            oauth_token,
                            oauth_secret)
        self.session = requests.Session()
        self.host = host
        self.scheme = scheme

    def url(self, endpoint):
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return "{0}://{1}{2}".format(self.scheme, self.host, endpoint)

    def __getattr__(self, attr):
        if attr in ("get", "post", "put", "delete", "patch", "head"):
            return functools.partial(self.request, attr)

        raise AttributeError(attr)

    def request(self, method, endpoint, **kwargs):
        if "auth" in kwargs:
            raise ValueError("request() called with auth")
        kwargs['auth'] = self.auth
        response = self.session.request(method, self.url(endpoint), **kwargs)
        response.raise_for_status()
        return response

