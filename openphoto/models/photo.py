#!/usr/bin/env python

import os
from time import mktime
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
    create_path = "/photo/upload.json"

    def __init__(self, client, data):
        super(Photo, self).__init__(client, data)
        size_mgr = PhotoSizeManager(self)
        object.__setattr__(self, "sizes", size_mgr)
        self._update_data(self.data)
        if not self._tags:
            object.__setattr__(self, "_tags", None)

    def _update_data(self, data):
        super(Photo, self)._update_data(data)
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
    def create(cls, client, photo, private=False, title=None,
               description=None, tags=None, date_uploaded=None,
               date_taken=None, license=None, latitude=None,
               longitude=None, return_sizes=None, albums=None,
               allow_duplicate=False):
        photo_f = None
        close_f = False
        try:
            if isinstance(photo, stringcls):
                close_f = True
                photo_f = open(photo)
            else:
                photo_f = photo

            permission = 0 if private else 1
            params = dict(permission=permission)
            if title:
                params["title"] = title
            if description:
                params["description"] = description
            if tags:
                params["tags"] = ",".join(tags)
            if date_uploaded:
                params["dateUploaded"] = mktime(date_uploaded.timetuple())
            if date_taken:
                params["dateTaken"] = mktime(date_taken.timetuple())
            if license:
                params["license"] = license
            if latitude:
                params["latitude"] = latitude
                if longitude:
                        params["longitude"] = longitude
                if return_sizes:
                    params["returnSizes"] = ",".join(return_sizes)
            if allow_duplicate:
                params["allowDuplicate"] = 1

            cls.log.info("Uploading from %s", photo_f)
            response = client.post(cls.create_path,
                                    files={"photo": photo_f}, params=params)

            obj = cls(client, response.json()["result"])
            if albums:
                obj.add_to(albums)
            return obj

        finally:
            if photo_f and close_f:
                photo_f.close()

    def add_to(self, albums):
        from .album import Album  # avoid circular imports
        if isinstance(albums, Album):
            albums = [albums]

        for album in albums:
            album.add(self)

    def add_comment(self, user_email, message, name=None, website=None,
                    target_url=None, permalink=None):
        """ Adds a comment to the photo """
        return Comment.create(self.client, self.id, user_email, message,
                             name, website, target_url, permalink)

    def favorite(self, user_email, message="", name=None, website=None,
                    target_url=None, permalink=None):
        """ Adds a favorite for the photo """
        return Favorite.create(self.client, self.id, user_email, message,
                              name, website, target_url, permalink)

    def download(self, destination=None, mode="wb", chunk_size=4096):
        """ Shortcut to download original photo """
        return self.sizes['original'].download(destination, mode, chunk_size)

    def nextprevious(self):
        """ Get next/previous photo(s) at once """
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
        """ Returns an iterator to iterate over next/previous """
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

    def replace(self, source):
        """ Replace the binary image file (and hash) """
        raise NotImplementedError()

    def transform(self, **kwargs):
        """ Transform a photo by rotating/BW/etc """
        url = self.url("transform")
        response = self.client.post(url, data=kwargs)
        self._update_data(response.json()["result"])
        return self

    @classmethod
    def update_batch(self, client, photos, data):
        """ Updates multiple photos at once """
        raise NotImplementedError()

    @classmethod
    def delete_batch(self, client, photos):
        """ Deletes multiple photos at once """
        raise NotImplementedError()
