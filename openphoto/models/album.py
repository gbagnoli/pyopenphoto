#!/usr/bin/env python

import functools
from .base import Base
from .photo import Photo
from ..utils import is_iterable_container


class Album(Base):
    collection_path = "/albums"
    object_path = "/album"

    def __init__(self, client, data):
        super(Album, self).__init__(client, data)
        self.cover = Photo(self.client, data['cover'])

    def photos(self):
        url = "{0}/album-{1}/list.json".format(Photo.collection_path, self.id)
        partial = functools.partial(self.client.request, "get", url)
        return self.iterate(self.client, partial, klass=Photo)

    @classmethod
    def create(self, **kwargs):
        # TODO
        raise NotImplementedError

    def _add_remove(self, action, photo):
        if is_iterable_container(photo):
            ids = ", ".join([str(p.id) for p in photo])
        else:
            ids = photo.id

        url = self.url("photo", action)
        self.client.post(url, data=dict(ids=ids))

    def add(self, photo):
        self._add_remove("add", photo)

    def remove(self, photo):
        self._add_remove("remove", photo)

