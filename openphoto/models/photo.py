#!/usr/bin/env python

import os
from .base import Base
from .action import (Comment,
                     Favorite)
from ..compat import stringcls


class Photo(Base):
    collection_path = "/photos"
    object_path = "/photo"
    create_path = "/photos/upload.json"

    def __init__(self, client, data):
        super(Photo, self).__init__(client, data)
        object.__setattr__(self, "_tags", None)
        self._set_paths()

    def view(self):
        super(Photo, self).view()
        self._set_paths()
        self._set_tags()

    def _set_paths(self):
        paths_keys = [k for k in self.data.keys() if k.startswith("path")]
        if not paths_keys:
            self._paths = None
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
        close_file = False
        file_ = destination
        try:
            if destination and isinstance(destination, stringcls):
                file_ = open(destination, mode)
                close_file = True

            url = self.url("download", extension=None)
            response = self.client.get(url, stream=True)
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
