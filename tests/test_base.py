#!/usr/bin/env python
from openphoto.models import Base
from compat import (mock,
                     unittest)


class TestBase(unittest.TestCase):

    def setUp(self):
        self.client = mock.MagicMock()

    def test_getattr(self):
        data = dict(attr1=1, attr2=2)
        obj = Base(self.client, data)
        self.assertIs(self.client, obj.client)
        self.assertDictEqual(obj.data, data)
        with self.assertRaises(AttributeError):
            obj.no_existing
        for attr in data:
            self.assertEqual(getattr(obj, attr), data[attr])

    def test_setattr(self):
        data = {}
        obj = Base(self.client, data)
        obj.new_attr = 1

        self.assertNotIn("new_attr", obj.data)
        self.assertIn("newAttr", obj.data)
        self.assertEqual(obj.new_attr, 1)
        self.assertEqual(obj.newAttr, 1)

    def test_create(self):
        ocp = Base.create_path
        try:
            Base.create_path = "/create_path"
            resp = self.client.post.return_value
            resp.json.return_value = dict(result=dict(res1=1,res2=2))
            obj = Base.create(self.client, attr1=1, attr2=2)
            self.assertIs(obj.data, resp.json.return_value['result'])
            self.assertTrue(self.client.post.called_with('/create_path', attr1=1, attr2=2))
        finally:
            Base.create_path = ocp

    def test_url(self):
        oop = Base.object_path
        try:
            Base.object_path = "/object"
            obj = Base(self.client, dict(id=1))
            self.assertEqual(obj.url("test"), "/object/1/test.json")
            self.assertEqual(obj.url("test", "multiple", "action"),
                             "/object/1/test/multiple/action.json")
            self.assertEqual(obj.url("test", "no", "ext", extension=None),
                             "/object/1/test/no/ext")
            with self.assertRaises(TypeError):
                obj.url("test", wrong="arg")

        finally:
            Base.create_path = oop

    @mock.patch.object(Base, "url")
    def test_delete(self, url_mock):
        obj = Base(self.client, {})
        res = obj.delete()
        self.assertTrue(self.client.post.return_value.json.called)
        self.assertIs(res, self.client.post.return_value.json.return_value)
        self.assertTrue(url_mock.called_with("delete"))
        self.assertTrue(self.client.post.called_with(url_mock.return_value))

    @mock.patch.object(Base, "url")
    def test_update(self, url_mock):
        params = dict(param1=1, param2=2)
        obj = Base(self.client, params)
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
        obj = Base(self.client, {"id":1})
        self.assertEqual(repr(obj), "<Base 1>")

    @mock.patch.object(Base, "search")
    def test_all(self, search_mock):
        self.assertIs(Base.all(self.client), search_mock.return_value)
        self.assertTrue(search_mock.called_with(self.client))

    @mock.patch.object(Base, "iterate")
    @mock.patch("functools.partial")
    def test_search(self, partial_mock, iterate_mock):
        ocp = Base.collection_path
        try:
            Base.collection_path = "/collection"
            params = dict(param1=1, param2=2)
            res = Base.search(self.client, **params)
            self.assertIs(res, iterate_mock.return_value)
            self.assertTrue(iterate_mock.called_with(self.client,
                                                     partial_mock.return_value))
            self.assertTrue(partial_mock.called_with(self.client.request, "get",
                                                     "/collection/list.json",
                                                     **params))
        finally:
            Base.collection_path = ocp

    def test_get(self):
        response_mock = mock.MagicMock()
        self.client.get.return_value = response_mock
        expected = dict(res1=1, res2=2)
        response_mock.json.return_value = dict(result=expected)
        obj = Base.get(self.client, "id")
        url = "{0}/id/view.json".format(Base.object_path)
        self.assertTrue(self.client.get.called_with(url))
        self.assertDictEqual(obj.data, expected)
        self.assertIs(self.client, obj.client)

    def test_iterate(self):
        partial = mock.MagicMock()
        expected = dict(res1=1, res2=2)
        resmock = mock.MagicMock()
        partial.return_value = resmock
        resmock.json.return_value = dict(result=[expected])

        iter_ = Base.iterate(self.client, partial)
        next_ = iter_.next if hasattr(iter_, "next") else iter_.__next__
        self.assertTrue(partial.called_with(params=dict(pageSize=Base.page_size,
                                                        page=1)))
        obj = next_()
        self.assertDictEqual(obj.data, expected)
        self.assertIs(obj.client, self.client)
        resmock.json.return_value = dict(result=[])
        with self.assertRaises(StopIteration):
            next_()
        self.assertTrue(partial.called_with(params=dict(pageSize=Base.page_size,
                                                        page=2)))

        expected2 = dict(res3=3, res4=4)
        partial = mock.MagicMock()
        resmock = mock.MagicMock()
        partial.return_value = resmock
        resmock.json.return_value = dict(result=[expected, expected2])
        klass = mock.MagicMock()
        res1, res2 = list(Base.iterate(self.client, partial, klass=klass, paginate=False))

        self.assertTrue(partial.called)
        self.assertIs(res1, klass.return_value)
        self.assertIs(res2, klass.return_value)

