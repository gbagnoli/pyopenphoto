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
        self.assertIsInstance(self.album.cover, Photo)
        self.assertDictEqual(self.album.cover.data, self.album.data['cover'])

    @mock.patch("functools.partial")
    @mock.patch.object(Base, "iterate")
    def test_photos(self, iterate_mock, partial_mock):
        self.assertIs(self.album._photos, None)
        res = self.album.photos()
        self.assertEqual(self.album._photos, [])
        self.assertIs(self.album._photos, res)
        view_url = self.album.url("view")
        self.assertTrue(self.client.get.called_with(view_url))

    def test_add_remove(self):
        objs = [Photo(self.client, {'id': 1}), Photo(self.client, {'id': 2})]
        add_url = "/album/myid/photo/add.json"
        remove_url = "/album/myid/photo/remove.json"

        self.album.add(objs)
        self.assertTrue(self.client.post.called_with(add_url,
                                                     data={'ids': "1,2"}))
        self.album.remove(objs)
        self.assertTrue(self.client.post.called_with(remove_url,
                                                     data={"ids": "1,2"}))
        self.album.remove(objs[0])
        self.assertTrue(self.client.post.called_with(remove_url,
                                                     data={"ids": "1"}))
