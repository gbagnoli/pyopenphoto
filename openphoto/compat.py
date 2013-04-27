#!/usr/bin/env python

try:
    stringcls = basestring
    stringcls  # pragma: no cover

except NameError:  # pragma: no cover
    stringcls = str


__all__ = ["stringcls"]
