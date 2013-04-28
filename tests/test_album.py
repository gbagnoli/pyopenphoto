#!/usr/bin/env python
from openphoto.models import Album, Photo, Base
from compat import (mock,
                    unittest)


class TestAlbum(unittest.TestCase):

    def setUp(self):
        self.client = mock.MagicMock()
        self.album_attr = dict(id="myid", name="myalbum", attr2=2, cover=dict(id="cover"))
        self.album = Album(self.client, self.album_attr)

    def test_cover(self):
        self.assertDictEqual(self.album.cover.data, dict(id="cover"))
        self.assertIsInstance(self.album.cover, Photo)

    @mock.patch("functools.partial")
    @mock.patch.object(Base, "iterate")
    def test_photos(self, iterate_mock, partial_mock):
        url = Photo.collection_path + "/album-myid/list.json"
        res = self.album.photos()
        self.assertIs(res, iterate_mock.return_value)
        self.assertTrue(partial_mock.called_with(self.client.request, "get", url))
        self.assertTrue(iterate_mock.called_with(self.client, partial_mock.return_value,
                                                 klass=Photo))

