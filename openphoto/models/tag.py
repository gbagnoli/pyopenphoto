#!/usr/bin/env python

from .base import (Base,
                   Relationship)
from .photo import Photo


class Tag(Base):
    collection_path = "/tags"
    object_path = "/tag"
    relationships = (Relationship("photos", Photo), )

    @classmethod
    def search(cls, client, paginate=False):
        if paginate:
            raise ValueError("Tag class does not support paginate in list")
        return super(Tag, cls).search(client, paginate=False)

    @classmethod
    def all(cls, client):
        return cls.search(client)

