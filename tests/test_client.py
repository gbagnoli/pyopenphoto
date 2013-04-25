try:
    import unittest2 as unittest
    unittest  # silence pyflakes

except ImportError:
    import unittest

try:
    import mock
    mock  # silence pyflakes
except ImportError:
    import unittest.mock as mock


from openphoto_utils.client import OpenphotoHttpClient


class TestClient(unittest.TestCase):

    @mock.patch("requests_oauthlib.OAuth1")
    @mock.patch("requests.Session")
    def setUp(self, session, oauth1):
        self.args = ("host", "ckey", "csecret", "otoken", "osecret", "http")
        self.client = OpenphotoHttpClient(*self.args)
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
        self.client.request(method, endpoint, first=True, last=False)
        self.assertTrue(msess_inst.request.called_with(method, url, first=True,
                                                       last=False, auth=self.mock_oauth1))
        response = msess_inst.request.return_value
        self.assertTrue(response.raise_for_status.called)

    def test_getattr(self):
        endpoint = "endpoint"
        url = self.client.url(endpoint)
        msess_inst = self.mock_session.return_value
        for attr in ("get", "post", "put", "delete", "patch", "head"):
            getattr(self.client, attr)(endpoint)
            self.assertTrue(
                msess_inst.request.called_with(attr, url, auth=self.mock_oauth1)
            )
            with self.assertRaises(AttributeError):
                self.client.not_existing

