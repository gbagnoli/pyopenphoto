#!/usr/bin/env python
from openphoto.models import Album, Photo
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
        self.assertFalse(isinstance(self.album.data['cover'], Photo))

        al = Album(self.client, {"id": "test"})
        self.assertIs(al.cover, None)

    def test_photos(self):
        self.assertTrue(len(self.album.photos) == 0)
        photos = [dict(first=1), dict(second=2)]
        info = dict(photos=photos)
        self.client.get.return_value.json.return_value = dict(result=info)
        self.album.refresh()
        self.assertEqual(len(self.album.photos), 2)
        self.assertIs(self.client, self.album.photos[0].client)
        self.assertEqual(self.album.photos[0].data, dict(first=1))
        self.assertIsInstance(self.album.photos[0], Photo)

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
