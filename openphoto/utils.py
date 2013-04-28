#!/usr/bin/env python

from collections import Iterable
from .compat import stringcls

def is_iterable(obj):
    """ Return True if object is an iterable (strings are iterables) """
    return isinstance(obj, Iterable)


def is_iterable_container(obj):
    """ Return true if obj is an iterable but not a string """
    return isinstance(obj, Iterable) and not isinstance(obj, stringcls)


def assert_kwargs_empty(kwargs):
    """ Raises TypeError if kwargs dict is not empty """
    if len(kwargs):
        fmt = "', '".join(list(kwargs.keys()))
        raise TypeError("'{0}': invalid keyword argument(s) for this function"
                        .format(fmt))

