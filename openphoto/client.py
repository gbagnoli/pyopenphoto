#!/usr/bin/env python
import functools
import logging
import traceback
import requests
import requests_oauthlib
try:
    import httplib
except ImportError:  # pragma: nocover
    import http.client as httplib


class Client(object):
    log = logging.getLogger(__name__)

    def __init__(self, host, consumer_key, consumer_secret,
                 oauth_token, oauth_secret, scheme="https",
                 http_debug_level=None):
        self.auth = requests_oauthlib.OAuth1(
                            consumer_key,
                            consumer_secret,
                            oauth_token,
                            oauth_secret)
        self.session = requests.Session()
        self.host = host
        self.scheme = scheme
        self.http_debug_level = http_debug_level

    @property
    def http_debug_level(self):
        return httplib.HTTPConnection.debuglevel

    @http_debug_level.setter
    def http_debug_level(self, value):
        if not value:
            value = 0
        httplib.HTTPConnection.debuglevel = int(value)

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
        return self.request_full_url(method, self.url(endpoint), **kwargs)

    def request_full_url(self, method, url, **kwargs):
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        try:
            jres = response.json()
            code = jres["code"]
            message = jres["message"]

        except:
            self.log.debug(traceback.format_exc())

        else:
            if 400 <= code < 500:
                message = '%s Client Error: %s' % (code, message)
            if 500 <= code < 600:
                message = '%s Server Error: %s' % (code, message)
            if 400 <= code < 600:
                raise requests.exceptions.HTTPError(message,
                                                    response=response)

        return response

