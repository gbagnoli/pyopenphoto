#!/usr/bin/env python
from .base import Base
from ..utils import assert_kwargs_empty


class Action(Base):

    @classmethod
    def search(cls, client, **kwargs):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    @classmethod
    def create(cls, client, photo_id, action_type, email, message,
               requests_args=None, **kwargs):

        url = "/action/{0}/photo/create.json".format(photo_id)

        if not action_type in ("comment", "favorite"):
            raise ValueError("Invalid action {0}".fotmat(action_type))

        if action_type == "favorite":
            klass = Favorite
        else:
            klass = Comment

        params = dict(email=email, value=message, type=action_type)
        for attr in ("name", "website", "target_url", "permalink"):
            value = kwargs.pop(attr, None)
            if value:
                params[cls._convert_attr(attr)] = value

        assert_kwargs_empty(kwargs)
        return super(Action, klass).create(client, path=url, **params)


class Favorite(Action):

    @classmethod
    def create(cls, client, photo_id, email, message="",
               request_args=None, **kwargs):
        super(Favorite, cls).create(client, photo_id, "favorite", email,
                                    message, **kwargs)


class Comment(Action):

    @classmethod
    def create(cls, client, photo_id, email, message,
               request_args=None, **kwargs):
        super(Favorite, cls).create(client, photo_id, "comment", email,
                                    message, **kwargs)

