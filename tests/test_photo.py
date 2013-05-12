#!/usr/bin/env python
from openphoto.models import Photo, Comment, Favorite, Tag
from compat import (mock,
                    unittest,
                    builtins_name)

open_name = "{0}.open".format(builtins_name)


class TestPhoto(unittest.TestCase):

    def setUp(self):
        self.client = mock.MagicMock()
        self.photo_attr = dict(id="myid", attr1=1, attr2=2,
                               pathOriginal="/my/path.jpg")
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

    @mock.patch(open_name)
    def test_download_to_fileobj(self, open_mock):
        file_mock = mock.Mock()
        icontent = self.client.get.return_value.iter_content
        icontent.return_value = ["1"]
        res = self.photo.download(destination=file_mock, mode="wb", chunk_size=1024)
        self.assertIs(res, None)
        self.assertFalse(open_mock.called)
        self.assertFalse(file_mock.close.called)
        self.assertTrue(self.client.get.called_with("/photo/myid/download", stream=True))
        self.assertTrue(icontent.called_with(chunk_size=1024))
        self.assertTrue(file_mock.write.called_with("1"))

    def test_download_iter(self):
        res_mock = self.client.request_full_url.return_value
        icontent = res_mock.iter_content
        res = self.photo.download(chunk_size=1024)
        self.assertIs(res, icontent.return_value)
        self.assertTrue(icontent.called_with(chunk_size=1024))

    @mock.patch(open_name)
    @mock.patch("os.unlink")
    def test_download_error_unlink(self, unlink_mock, open_mock):
        self.client.request_full_url.configure_mock(side_effect=OSError)
        with self.assertRaises(OSError):
            self.photo.download("destination")

        self.assertTrue(unlink_mock.called_with("destination"))

    @mock.patch(open_name)
    @mock.patch("os.unlink")
    def test_download_error_fileobj(self, unlink_mock, open_mock):
        file_mock = mock.Mock()
        self.client.request_full_url.configure_mock(side_effect=OSError)
        with self.assertRaises(OSError):
            self.photo.download(destination=file_mock)

        self.assertFalse(unlink_mock.called)
        self.assertFalse(open_mock.called)

    def test_paths(self):
        self.assertEqual(self.photo._paths, {"original": "/my/path.jpg"})
        object.__setattr__(self.photo, "_paths", None)
        self.client.get.return_value.json.return_value = {
            "result": {
                "path1": r"http:\/\/test/url",
                "path2": "2"
            }
        }
        paths = self.photo.paths()
        self.assertEqual(paths, {"1":"http://test/url", "2":"2"})
        self.assertIs(paths, self.photo._paths)

    def test_tags(self):
        self.assertEqual(self.photo._tags, None)
        self.client.get.return_value.json.return_value = {
            "result": {
                "tags": ["a", "b"]
            }
        }
        tags = self.photo.tags()
        self.assertEqual(len(tags), 2)
        self.assertIsInstance(tags[0], Tag)
        self.assertEqual(tags[0].id, "a")
        self.assertEqual(tags[1].id, "b")
        self.assertIs(self.photo._tags, tags)

    def test_albums(self):
        with self.assertRaises(NotImplementedError):
            self.photo.albums()

    def test_nextprev(self):
        self.client.get.return_value.json.return_value = {"result": {}}
        res = self.photo.nextprevious()
        self.assertEqual(res['next'], res['previous'])
        self.assertEqual(res['next'], [])
        self.client.get.return_value.json.return_value = {
            "result": {
                "next": [{"id": 1}, {"id": 2}],
                "previous": [{"id": 3}, {"id": 4}]
            }
        }
        res = self.photo.nextprevious()
        nx = self.photo.get_next()
        pv = self.photo.get_previous()
        for i in range(2):
            self.assertEqual(nx[i].id, res['next'][i].id)
            self.assertEqual(pv[i].id, res['previous'][i].id)

    def test_stream(self):
        json = self.client.get.return_value.json
        json.return_value ={"result": {}}
        g = self.photo.stream()
        if hasattr(g, "next"):
            met = "next"
        else:
            met = "__next__"
        with self.assertRaises(StopIteration):
            getattr(g, met)()

        g = self.photo.stream(reverse=True)
        with self.assertRaises(StopIteration):
            getattr(g, met)()

        json.return_value = {"result": {"next": [{"id": 1}]}}

        g = self.photo.stream()
        p = getattr(g, met)()

        self.assertEqual(p.id, 1)

        json.return_value = {"result": {"next": [{"id": 2}]}}
        p = getattr(g, met)()
        self.assertEqual(p.id, 2)

        json.return_value = {"result": {}}
        with self.assertRaises(StopIteration):
            getattr(g, met)()
