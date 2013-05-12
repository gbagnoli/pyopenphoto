#!/usr/bin/env python

import functools
from .base import Base
from .photo import Photo


class Tag(Base):
    collection_path = "/tags"
    object_path = "/tag"

    @classmethod
    def all(cls, client):
        return super(Tag, cls).all(client, paginate=False)

    def photos(self, **kwargs):
        url = "{0}/tags-{1}/list.json".format(Photo.collection_path, self.id)
        partial = functools.partial(self.client.request, "get", url, **kwargs)
        return self.iterate(self.client, partial, klass=Photo)

