#!/usr/bin/env python

import requests
from .base import Base
from .photo import Photo
from ..utils import is_iterable_container


class Album(Base):
    collection_path = "/albums"
    object_path = "/album"
    create_path = "/album/create.json"

    def __init__(self, client, data):
        super(Album, self).__init__(client, data)
        if "cover" in data and data["cover"]:
            cover = Photo(self.client, data['cover'])
        else:
            cover = None
        object.__setattr__(self, "cover", cover)
        object.__setattr__(self, "_photos", None)
        try:
            # fixes updates
            del self.data["count"]
        except KeyError:
            pass

    def _set_photos(self):
        object.__setattr__(
            self, "_photos",
            [Photo(self.client, d) for d in self.data["photos"]]
        )

    @classmethod
    def get(cls, client, id=None, name=None, **kwargs):
        if id:
            return super(Album, cls).get(client, id, **kwargs)

        if name:
            url = "{0}/list.json".format(cls.collection_path)
            params = kwargs
            response = client.get(url, params=params)
            albums = response.json()["result"]
            for album in albums:
                if album["name"] == name:
                    return cls(client, album)

            raise requests.exceptions.HTTPError("404 Client Error: Not Found",
                                                response=response)

        raise TypeError("Missing one of id or name")

    def photos(self):
        if self._photos is None:
            self.view()
            self._set_photos()

        return self._photos

    def view(self):
        super(Album, self).view()
        self._set_photos()

    @classmethod
    def create(cls, client, name, return_existing=False):
        if return_existing:
            try:
                return cls.get(client, name=name)

            except requests.exceptions.HTTPError as e:
                cls.log.critical(e.response.status_code)
                if e.response.status_code == 404:
                    pass
                else:
                    raise e

        return super(Album, cls).create(client,
                                        name=name)

    def _add_remove(self, action, photo):
        if is_iterable_container(photo):
            ids = ", ".join([str(p.id) for p in photo])
        else:
            ids = photo.id

        url = self.url("photo", action)
        self.client.post(url, data=dict(ids=ids))
        object.__setattr__(self, "_photos", None)

    def add(self, photo):
        self._add_remove("add", photo)

    def remove(self, photo):
        self._add_remove("remove", photo)

    def __repr__(self):
        return "<Album id={self.id} name={self.name}>".format(self=self)

