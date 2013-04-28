#!/usr/bin/env python
import functools
from ..utils import assert_kwargs_empty
from ..compat import stringcls


class Relationship(object):

    def __init__(self, attribute, klass, type="many"):
        self.attribute = attribute
        self.klass = klass
        if type not in ("many", "single"):
            raise ValueError("Invalid relation type '%s'" % (type))

        self.type = type

    def resolve(self, klass):
        if not isinstance(klass, stringcls):
            return klass

        mname, clsname = klass.rsplit(".", 1)
        module = __import__(mname, fromlist=[clsname])
        return getattr(module, clsname)

    def to_obj(self, client, data):
        self.klass = self.resolve(self.klass)
        if self.type == "many":
            return [self.klass(client, d) for d in data]
        else:
            return self.klass(client, data)


class Base(object):
    page_size = 100
    collection_path = None
    object_path = None
    create_path = None
    relationships = tuple()

    @classmethod
    def iterate(cls, client, partial, klass=None, paginate=True):
        klass = klass or cls
        if paginate:
            page = 1
            result = True
            while result:
                data = dict(pageSize=cls.page_size, page=page)
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
        self._update_relationships()

    def _update_relationships(self):
        for r in self.relationships:
            if r.attribute in self.data and self.data[r.attribute]:
                value = r.to_obj(self.client, self.data[r.attribute])
            else:
                if r.type == "many":
                    value = []
                else:
                    value = None

            object.__setattr__(self, r.attribute, value)

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
    def get(cls, client, id):
        obj = cls(client, {"id":id})
        return obj.view()

    @classmethod
    def search(cls, client, paginate=True, **kwargs):
        url = "{0}/list.json".format(cls.collection_path)
        partial = functools.partial(client.request, "get", url, **kwargs)
        return cls.iterate(client, partial, paginate=paginate)

    @classmethod
    def all(cls, client, paginate=True):
        return cls.search(client, paginate)

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

    save = update

    def view(self):
        params = dict(includeElements=1)
        response = self.client.get(self.url("view"), params=params)
        data = response.json()['result']
        object.__setattr__(self, "data", data)
        self._update_relationships()
        return self

    refresh = view

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.id)

