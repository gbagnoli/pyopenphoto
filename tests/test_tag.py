#!/usr/bin/env python
from openphoto.models import Base, Tag, Photo
from compat import (mock,
                    unittest)


class TestTag(unittest.TestCase):

    def setUp(self):
        self.client = mock.MagicMock()
        self.tag_attr = dict(id="mytag", attr1=1, attr2=2)
        self.tag = Tag(self.client, self.tag_attr)

    @mock.patch.object(Base, "all")
    def test_all(self, super_all):
        with self.assertRaises(TypeError):
            Tag.all(self.client, paginate=True)

        res = Tag.all(self.client)
        self.assertIs(res, super_all.return_value)
        res = Tag.all(self.client)
        self.assertIs(res, super_all.return_value)

    @mock.patch("functools.partial")
    @mock.patch.object(Base, "iterate")
    def test_photos(self, iterate_mock, partial_mock):
        args = dict(arg1=1, arg2=2)
        url = Photo.collection_path + "/tags-mytag/list.json"
        res = self.tag.photos(**args)
        self.assertIs(res, iterate_mock.return_value)
        self.assertTrue(iterate_mock.called_with(self.client, partial_mock.return_value,
                                                 klass=Photo))
        self.assertTrue(partial_mock.called_with(self.client.request, "get", url, **args))

