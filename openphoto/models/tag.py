#!/usr/bin/env python

import functools
from .base import Base
from .photo import Photo


class Tag(Base):
    collection_path = "/tags"
    object_path = "/tag"

    @classmethod
    def search(cls, client, paginate=False):
        if paginate:
            raise ValueError("Tag class does not support paginate in list")
        return super(Tag, cls).search(client, paginate=False)

    @classmethod
    def all(cls, client):
        return cls.search(client)

    def photos(self, **kwargs):
        url = "{0}/tags-{1}/list.json".format(Photo.collection_path, self.id)
        partial = functools.partial(self.client.request, "get", url, **kwargs)
        return self.iterate(self.client, partial, klass=Photo)

