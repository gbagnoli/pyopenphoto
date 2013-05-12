#!/usr/bin/env python

import os
from .base import Base
from .action import (Comment,
                     Favorite)
from ..compat import stringcls


class PhotoSizeManager(object):

    def __init__(self, photo):
        self.client = photo.client
        self.photo = photo

    def get_sizes(self, sizes):
        if isinstance(sizes, stringcls):
            sizes = [sizes]
        returnSizes = ",".join(sizes)
        if self.photo._paths is None:
            self.photo.view(returnSizes=returnSizes)

        else:
            sizes_set = set(sizes)
            if sizes_set & set(self.photo._paths) != sizes_set:
                self.photo.view(returnSizes=returnSizes)

        return [PhotoSize(self.photo.paths()[s], self.client, self.photo)
                for s in sizes]

    def __getitem__(self, size):
        return self.get_sizes(size)[0]


class PhotoSize(object):

    def __init__(self, url, client, photo):
        self.client = client
        self.photo = photo
        self.url = url

    def download(self, destination=None, mode="wb", chunk_size=4096):
        close_file = False
        file_ = destination
        try:
            if destination and isinstance(destination, stringcls):
                file_ = open(destination, mode)
                close_file = True

            response = self.client.request_full_url("get", self.url, stream=True)
            if destination:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    file_.write(chunk)
            else:
                return response.iter_content(chunk_size=chunk_size)

        except Exception as e:
            try:
                if close_file:
                    os.unlink(destination)

            except:  # pragma: nocover
                pass

            finally:
                raise e

        finally:
            if close_file:
                file_.close()


class Photo(Base):
    collection_path = "/photos"
    object_path = "/photo"
    create_path = "/photos/upload.json"

    def __init__(self, client, data):
        super(Photo, self).__init__(client, data)
        object.__setattr__(self, "_tags", None)
        size_mgr = PhotoSizeManager(self)
        object.__setattr__(self, "sizes", size_mgr)
        self._set_paths()

    def view(self, **kwargs):
        super(Photo, self).view(**kwargs)
        self._set_paths()
        self._set_tags()

    def _set_paths(self):
        paths_keys = [k for k in self.data.keys() if k.startswith("path")]
        if not paths_keys:
            object.__setattr__(self, "_paths", None)
            return

        paths = {}
        for k in paths_keys:
            key = k.replace("path", "").lower()
            paths[key] = self.data[k].replace("\\", "")
            del self.data[k]

        object.__setattr__(self, "_paths", paths)

    def _set_tags(self):
        from .tag import Tag  # avoid circular imports
        if "tags" in self.data:
            tags_ids = self.data['tags']
        else:
            tags_ids = []
        tags = [Tag(self.client, {"id": data}) for data in tags_ids]
        object.__setattr__(self, "_tags", tags)

    def albums(self):
        raise NotImplementedError("Remote API does not provide this information")

    def paths(self):
        if self._paths is None:
            self.view()

        return self._paths

    def tags(self):
        if self._tags is None:
            self.view()
            self._set_tags()

        return self._tags

    @classmethod
    def create(cls, client, **kwargs):
        # TODO
        raise NotImplementedError

    def add_comment(self, user_email, message, name=None, website=None,
                    target_url=None, permalink=None):
       return Comment.create(self.client, self.id, user_email, message,
                             name, website, target_url, permalink)

    def favorite(self, user_email, message="", name=None, website=None,
                    target_url=None, permalink=None):
       return Favorite.create(self.client, self.id, user_email, message,
                              name, website, target_url, permalink)

    def download(self, destination=None, mode="wb", chunk_size=4096):
        return self.sizes['original'].download(destination, mode, chunk_size)

    def nextprevious(self):
        cls = self.__class__
        url = self.url("nextprevious", "list")
        response = self.client.get(url).json()["result"]
        result = {}
        for k in ("next", "previous"):
            if not k in response:
                result[k] = []
            else:
                result[k] = [cls(self.client, d) for d in response[k]]
        return result

    def get_next(self):
        return self.nextprevious()['next']

    def get_previous(self):
        return self.nextprevious()['previous']

    def stream(self, reverse=False):
        key = "next"
        if reverse:
            key = "previous"

        current = self
        while True:
            nxpv = current.nextprevious()
            if not nxpv[key]:
                raise StopIteration()
            yield nxpv[key][0]
            current = nxpv[key][0]

