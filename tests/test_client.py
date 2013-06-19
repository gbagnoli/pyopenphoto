#!/usr/bin/env python

import requests
from openphoto import Client
from compat import (mock,
                     unittest)


class TestClient(unittest.TestCase):

    @mock.patch("requests_oauthlib.OAuth1")
    @mock.patch("requests.Session")
    def setUp(self, session, oauth1):
        self.args = ("host", "ckey", "csecret", "otoken", "osecret", "http", 10)
        self.client = Client(*self.args)
        self.mock_session = session
        self.mock_oauth1 = oauth1

    def test_init(self):
        self.assertTrue(hasattr(self.client, "auth"))
        self.assertTrue(self.mock_oauth1.called_with(*self.args))
        self.assertTrue(hasattr(self.client, "session"))
        self.assertTrue(self.mock_session.called)
        self.assertEqual(self.client.host, "host")
        self.assertEqual(self.mock_session.return_value, self.client.session)
        self.assertEqual(self.mock_oauth1.return_value, self.client.auth)
        self.assertEqual(self.client.http_debug_level, 10)

    def test_http_debug_level(self):
        for value_set, expected in ((20, 20), (None, 0), ("30", 30)):
            self.client.http_debug_level = value_set
            self.assertEqual(self.client.http_debug_level, expected)

        with self.assertRaises(ValueError):
            self.client.http_debug_level = "a"

    def test_url(self):
        expected = "http://host/test"
        self.assertEqual(self.client.url("/test"), expected)
        self.assertEqual(self.client.url("test"), expected)

    def test_request(self):
        method = "mymethod"
        endpoint = "endpoint"
        url = self.client.url(endpoint)
        self.assertRaises(ValueError, self.client.request, method, endpoint, auth=True)

        msess_inst = self.mock_session.return_value
        response = msess_inst.request.return_value
        response.json.return_value = dict()
        self.client.request(method, endpoint, first=True, last=False)
        self.assertTrue(msess_inst.request.called_with(method, url, first=True,
                                                       last=False, auth=self.mock_oauth1))
        self.assertTrue(response.raise_for_status.called)

        response.json.return_value = dict(code=500,
                                          message="test exc")
        with self.assertRaises(requests.exceptions.HTTPError) as cm:
            self.client.request(method, endpoint)
        self.assertEqual(str(cm.exception), "500 Server Error: test exc")

        response.json.return_value = dict(code=400,
                                          message="test exc")
        with self.assertRaises(requests.exceptions.HTTPError) as cm:
            self.client.request(method, endpoint)
        self.assertEqual(str(cm.exception), "400 Client Error: test exc")


        msess_inst.request.return_value.json.side_effect = Exception("Fake")
        res = self.client.request(method, endpoint)
        self.assertEqual(res, response)


    def test_getattr(self):
        endpoint = "endpoint"
        url = self.client.url(endpoint)
        msess_inst = self.mock_session.return_value
        response = msess_inst.request.return_value
        response.json.return_value = dict()
        for attr in ("get", "post", "put", "delete", "patch", "head"):
            getattr(self.client, attr)(endpoint)
            self.assertTrue(
                msess_inst.request.called_with(attr, url, auth=self.mock_oauth1)
            )
            with self.assertRaises(AttributeError):
                self.client.not_existing


