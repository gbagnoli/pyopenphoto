#!/usr/bin/env python
from openphoto.models import Base, Tag, Photo
from compat import (mock,
                    unittest)


class TestTag(unittest.TestCase):

    def setUp(self):
        self.client = mock.MagicMock()
        self.tag_attr = dict(id="mytag", attr1=1, attr2=2)
        self.tag = Tag(self.client, self.tag_attr)

    @mock.patch.object(Base, "search")
    def test_search(self, super_search):
        with self.assertRaises(ValueError):
            Tag.search(self.client, paginate=True)

        res = Tag.search(self.client)
        self.assertIs(res, super_search.return_value)
        res = Tag.all(self.client)
        self.assertIs(res, super_search.return_value)

    def test_photos(self):
        self.assertTrue(len(self.tag.photos) == 0)
        photos = [dict(first=1), dict(second=2)]
        info = dict(photos=photos)
        self.client.get.return_value.json.return_value = dict(result=info)
        self.tag.refresh()
        self.assertEqual(len(self.tag.photos), 2)
        self.assertIs(self.client, self.tag.photos[0].client)
        self.assertEqual(self.tag.photos[0].data, dict(first=1))
        self.assertIsInstance(self.tag.photos[0], Photo)

