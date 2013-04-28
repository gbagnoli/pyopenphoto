#!/usr/bin/env python

import os
from .base import (Base,
                   Relationship)
from .action import (Comment,
                     Favorite)
from ..compat import stringcls


class Photo(Base):
    collection_path = "/photos"
    object_path = "/photo"
    create_path = "/photos/upload.json"
    relationships = (Relationship("albums", "openphoto.models.Album"),
                     Relationship("tags", "openphoto.models.Tag"))

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
