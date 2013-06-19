#!/usr/bin/env python

from .base import Base
from .photo import Photo
from ..utils import is_iterable_container


class Album(Base):
    collection_path = "/albums"
    object_path = "/album"

    def __init__(self, client, data):
        super(Album, self).__init__(client, data)
        if "cover" in data and data["cover"]:
            cover = Photo(self.client, data['cover'])
        else:
            cover = None
        object.__setattr__(self, "cover", cover)
        object.__setattr__(self, "_photos", None)

    def _set_photos(self):
        object.__setattr__(
            self, "_photos",
            [Photo(self.client, d) for d in self.data["photos"]]
        )

    def photos(self):
        if self._photos is None:
            self.view()
            self._set_photos()

        return self._photos

    def view(self):
        super(Album, self).view()
        self._set_photos()

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

