#!/usr/bin/env python
import functools
from ..utils import assert_kwargs_empty


class Base(object):
    page_size = 100
    collection_path = None
    object_path = None
    create_path = None

    @classmethod
    def iterate(cls, client, partial, klass=None, paginate=True):
        klass = klass or cls
        if paginate:
            page = 1
            result = True
            while result:
                data = dict(pageSize=cls.page_size, page=page)
                if "params" in partial.keywords:
                    data.update(partial.keywords['params'])
                result = partial(params=data).json()['result']
                for data in result:
                    yield klass(client, data)

                page = page + 1
        else:
            result = partial().json()['result']
            for data in result:
                yield klass(client, data)

    def __init__(self, client, data):
        object.__setattr__(self, "client", client)
        object.__setattr__(self, "data", data)

    def _convert_attr(self, attr):
        if "_" in attr:
            attrname = attr.replace("_", " ").title().replace(" ", "")
            attrname = attrname[0].lower() + attrname[1:]
        else:
            attrname = attr

        return attrname

    def __getattr__(self, attr):
        attrname = self._convert_attr(attr)
        try:
            return self.data[attrname]

        except KeyError:
            raise AttributeError(attr)

    def __setattr__(self, attr, value):
        attr = self._convert_attr(attr)
        self.data[attr] = value

    @classmethod
    def create(cls, client, path=None, requests_args=None, **kwargs):
        requests_args = requests_args or {}
        data = requests_args.pop("data", {})
        kwargs.update(data)
        path = path or cls.create_path
        response = client.post(path, data=kwargs, **requests_args)
        return cls(client, response.json()['result'])

    @classmethod
    def get(cls, client, id, **kwargs):
        obj = cls(client, {"id":id})
        obj.view(**kwargs)
        return obj

    def view(self, **kwargs):
        params = dict(includeElements=1)
        params.update(kwargs)
        response = self.client.get(self.url("view"), params=params)
        data = response.json()['result']
        object.__setattr__(self, "data", data)
        return self

    refresh = view

    @classmethod
    def all(cls, client, paginate=True, **kwargs):
        url = "{0}/list.json".format(cls.collection_path)
        params = kwargs
        partial = functools.partial(client.request, "get", url, params=params)
        return cls.iterate(client, partial, paginate=paginate)

    list = all

    def url(self, *path, **kwargs):
        extension = kwargs.pop("extension", ".json") or ""
        assert_kwargs_empty(kwargs)
        path = "/".join(path)

        return "{0}/{1}/{2}{3}".format(self.object_path, self.id, path,
                                       extension)

    def delete(self):
        return self.client.post(self.url("delete")).json()

    def update(self):
        return self.client.post(self.url("update"), data=self.data).json()

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.id)
