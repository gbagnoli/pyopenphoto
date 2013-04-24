
import functools
import requests
import requests_oauthlib


class OpenphotoHttpClient(object):

    def __init__(self, host, consumer_key, consumer_secret,
                       oauth_token, oauth_secret, scheme="https"):
        self.auth = requests_oauthlib.OAuth1(
                            consumer_key,
                            consumer_secret,
                            oauth_token,
                            oauth_secret)
        self.session = requests.Session()
        self.host = host
        self.scheme = scheme

    def url(self, endpoint):
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return "{0}://{1}{2}".format(self.scheme, self.host, endpoint)

    def __getattr__(self, attr):
        if attr in ("get", "post", "put", "delete", "patch", "head"):
            return functools.partial(self.request, attr)

        raise AttributeError(attr)

    def request(self, method, endpoint, **kwargs):
        if "auth" in kwargs:
            raise ValueError("request() called with auth")
        kwargs['auth'] = self.auth
        response = self.session.request(method, self.url(endpoint), **kwargs)
        response.raise_for_status()
        return response


class OpenPhotoObject(object):
    page_size = 100
    collection_path = None
    object_path = None
    create_path = None

    @classmethod
    def iterate(cls, client, partial):
        page = 1
        result = True
        while result:
            data = dict(pageSize=cls.page_size, page=page)
            result = partial(params=data).json()['result']
            for data in result:
                yield cls(client, data)

            page = page + 1

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
    def create(cls, client, **kwargs):
        response = client.post(cls.create_path, **kwargs)
        return cls(client, response.json())

    @classmethod
    def all(cls, client):
        return cls.search(client)

    @classmethod
    def search(cls, client, **kwargs):
        url = "{}/list.json".format(cls.collection_path)
        partial = functools.partial(client.request, "get", url, **kwargs)
        return cls.iterate(client, partial)

    def url(self, operation):
        return "{0}/{1}/{2}.json".format(self.object_path, self.id, operation)

    def delete(self):
        return self.client.post(self.url("delete")).json()

    def update(self):
        return self.client.post(self.url("update"), data=self.data).json()

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self.id)


class Photo(OpenPhotoObject):
    collection_path = "/photos"
    object_path = "/photo"
    create_path = "/photos/upload.json"

    @classmethod
    def create(cls, client, **kwargs):
        raise NotImplementedError
