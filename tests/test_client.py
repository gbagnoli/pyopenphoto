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


from openphoto_utils.client import (OpenphotoHttpClient,
                                    OpenPhotoObject)


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


class TestOpenPhotoObject(unittest.TestCase):

    def setUp(self):
        self.client = mock.MagicMock()

    def test_getattr(self):
        data = dict(attr1=1, attr2=2)
        obj = OpenPhotoObject(self.client, data)
        self.assertIs(self.client, obj.client)
        self.assertDictEqual(obj.data, data)
        with self.assertRaises(AttributeError):
            obj.no_existing
        for attr in data:
            self.assertEqual(getattr(obj, attr), data[attr])

    def test_setattr(self):
        data = {}
        obj = OpenPhotoObject(self.client, data)
        obj.new_attr = 1

        self.assertNotIn("new_attr", obj.data)
        self.assertIn("newAttr", obj.data)
        self.assertEqual(obj.new_attr, 1)
        self.assertEqual(obj.newAttr, 1)

    def test_create(self):
        ocp = OpenPhotoObject.create_path
        try:
            OpenPhotoObject.create_path = "/create_path"
            resp = self.client.post.return_value
            resp.json.return_value = dict(result=dict(res1=1,res2=2))
            obj = OpenPhotoObject.create(self.client, attr1=1, attr2=2)
            self.assertIs(obj.data, resp.json.return_value['result'])
            self.assertTrue(self.client.post.called_with('/create_path', attr1=1, attr2=2))
        finally:
            OpenPhotoObject.create_path = ocp

    def test_url(self):
        oop = OpenPhotoObject.object_path
        try:
            OpenPhotoObject.object_path = "/object"
            obj = OpenPhotoObject(self.client, dict(id=1))
            self.assertEqual(obj.url("test"), "/object/1/test.json")
        finally:
            OpenPhotoObject.create_path = oop

    @mock.patch.object(OpenPhotoObject, "url")
    def test_delete(self, url_mock):
        obj = OpenPhotoObject(self.client, {})
        res = obj.delete()
        self.assertTrue(self.client.post.return_value.json.called)
        self.assertIs(res, self.client.post.return_value.json.return_value)
        self.assertTrue(url_mock.called_with("delete"))
        self.assertTrue(self.client.post.called_with(url_mock.return_value))

    @mock.patch.object(OpenPhotoObject, "url")
    def test_update(self, url_mock):
        params = dict(param1=1, param2=2)
        obj = OpenPhotoObject(self.client, params)
        res = obj.update()
        self.assertTrue(self.client.post.return_value.json.called)
        self.assertIs(res, self.client.post.return_value.json.return_value)
        self.assertTrue(url_mock.called_with("update"))
        self.assertTrue(self.client.post.called_with(url_mock.return_value,
                        data=params))
        obj.data["param3"] = 3
        del obj.data["param2"]
        self.assertTrue(self.client.post.called_with(url_mock.return_value,
                                                     data=dict(param1=1, param3=3)))

    def test_repr(self):
        obj = OpenPhotoObject(self.client, {"id":1})
        self.assertEqual(repr(obj), "<OpenPhotoObject 1>")

    @mock.patch.object(OpenPhotoObject, "search")
    def test_all(self, search_mock):
        self.assertIs(OpenPhotoObject.all(self.client), search_mock.return_value)
        self.assertTrue(search_mock.called_with(self.client))

    @mock.patch.object(OpenPhotoObject, "iterate")
    @mock.patch("functools.partial")
    def test_search(self, partial_mock, iterate_mock):
        ocp = OpenPhotoObject.collection_path
        try:
            OpenPhotoObject.collection_path = "/collection"
            params = dict(param1=1, param2=2)
            res = OpenPhotoObject.search(self.client, **params)
            self.assertIs(res, iterate_mock.return_value)
            self.assertTrue(iterate_mock.called_with(self.client,
                                                     partial_mock.return_value))
            self.assertTrue(partial_mock.called_with(self.client.request, "get",
                                                     "/collection/list.json",
                                                     **params))
        finally:
            OpenPhotoObject.collection_path = ocp

    def test_get(self):
        response_mock = mock.MagicMock()
        self.client.get.return_value = response_mock
        expected = dict(res1=1, res2=2)
        response_mock.json.return_value = dict(result=expected)
        obj = OpenPhotoObject.get(self.client, "id", "test.json")
        url = "{0}/id/test.json".format(OpenPhotoObject.object_path)
        self.assertTrue(self.client.get.called_with(url))
        self.assertDictEqual(obj.data, expected)
        self.assertIs(self.client, obj.client)

    def test_iterate(self):
        partial = mock.MagicMock()
        expected = dict(res1=1, res2=2)
        resmock = mock.MagicMock()
        partial.return_value = resmock
        resmock.json.return_value = dict(result=[expected])

        iter_ = OpenPhotoObject.iterate(self.client, partial)
        next_ = iter_.next if hasattr(iter_, "next") else iter_.__next__
        self.assertTrue(partial.called_with(params=dict(pageSize=OpenPhotoObject.page_size,
                                                        page=1)))
        obj = next_()
        self.assertDictEqual(obj.data, expected)
        self.assertIs(obj.client, self.client)
        resmock.json.return_value = dict(result=[])
        with self.assertRaises(StopIteration):
            next_()
        self.assertTrue(partial.called_with(params=dict(pageSize=OpenPhotoObject.page_size,
                                                        page=2)))

