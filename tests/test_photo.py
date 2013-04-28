#!/usr/bin/env python
from openphoto.models import Photo, Comment, Favorite
from compat import (mock,
                    unittest,
                    builtins_name)

open_name = "{0}.open".format(builtins_name)


class TestPhoto(unittest.TestCase):

    def setUp(self):
        self.client = mock.MagicMock()
        self.photo_attr = dict(id="myid", attr1=1, attr2=2)
        self.photo = Photo(self.client, self.photo_attr)

    @mock.patch.object(Comment, "create")
    def test_add_comment(self, create_mock):
        args = dict(user_email="email", message="message", name="name",
                    website="website", target_url="tlink", permalink="perma")
        self.photo.add_comment(**args)
        self.assertTrue(create_mock.called_with(self.client, "myid", **args))

    @mock.patch.object(Favorite, "create")
    def test_favorite(self, create_mock):
        args = dict(user_email="email", message="message", name="name",
                    website="website", target_url="tlink", permalink="perma")
        self.photo.favorite(**args)
        self.assertTrue(create_mock.called_with(self.client, "myid", **args))

    @mock.patch(open_name)
    def test_download_to_file(self, open_mock):
        file_mock = open_mock.return_value
        icontent = self.client.get.return_value.iter_content
        icontent.return_value = ["1"]
        res = self.photo.download(destination="filename", mode="wb", chunk_size=1024)
        self.assertIs(res, None)
        self.assertTrue(file_mock.close.called)
        self.assertTrue(self.client.get.called_with("/photo/myid/download", stream=True))
        self.assertTrue(icontent.called_with(chunk_size=1024))
        self.assertTrue(file_mock.write.called_with("1"))

    def test_download_iter(self):
        res_mock = self.client.get.return_value
        icontent = res_mock.iter_content
        res = self.photo.download(chunk_size=1024)
        self.assertIs(res, icontent.return_value)
        self.assertTrue(icontent.called_with(chunk_size=1024))

    @mock.patch(open_name, side_effect=OSError)
    @mock.patch("os.unlink")
    def test_download_unlink(self, unlink_mock, open_mock):
        with self.assertRaises(OSError):
            self.photo.download("destination")

        self.assertTrue(unlink_mock.called_with("destination"))

