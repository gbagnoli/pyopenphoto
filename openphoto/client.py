
import functools
import requests
import requests_oauthlib

try:
    stringcls = basestring
    stringcls  # pragma: no cover

except NameError:  # pragma: no cover
    stringcls = str

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
    def get(cls, client, id, endpoint="view.json"):
        response = client.get("{0}/{1}/{2}".format(cls.object_path, id, endpoint))
        data = response.json()['result']
        return cls(client, data)

    @classmethod
    def search(cls, client, paginate=True, **kwargs):
        url = "{0}/list.json".format(cls.collection_path)
        partial = functools.partial(client.request, "get", url, **kwargs)
        return cls.iterate(client, partial, paginate=paginate)

    @classmethod
    def all(cls, client, paginate=True):
        return cls.search(client, paginate)

    list = all

    def url(self, operation, extension=".json"):
        extension = extension or ""
        return "{0}/{1}/{2}{3}".format(self.object_path, self.id, operation,
                                       extension)

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

        finally:
            if close_file:
                file_.close()


class Action(OpenPhotoObject):

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

        if len(kwargs):
            fmt = "', '".join(list(kwargs.keys()))
            raise TypeError(
                "'{0}': invalid keyword argument for this function".format(fmt))

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


class Album(OpenPhotoObject):
    collection_path = "/albums"
    object_path = "/album"

    def __init__(self, client, data):
        super(Album, self).__init__(client, data)
        self.cover = Photo(self.client, data['cover'])

    def photos(self):
        url = "{0}/album-{1}/list.json".format(Photo.collection_path, self.id)
        partial = functools.partial(self.client.request, "get", url)
        return self.iterate(self.client, partial, klass=Photo)

    @classmethod
    def create(self, **kwargs):
        # TODO
        raise NotImplementedError


class Tag(OpenPhotoObject):
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

