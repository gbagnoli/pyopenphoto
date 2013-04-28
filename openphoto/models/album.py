#!/usr/bin/env python

from .base import (Base,
                   Relationship)
from .photo import Photo
from ..utils import is_iterable_container


class Album(Base):
    collection_path = "/albums"
    object_path = "/album"
    relationships = (Relationship("photos", Photo),
                     Relationship("cover", Photo, "single"))

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

