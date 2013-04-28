#!/usr/bin/env python
import sys

PY3 = sys.version_info[0] == 3

if PY3:  # pragma: no cover
    stringcls = str

else:  # pragma: no cover
    stringcls = basestring


__all__ = ["stringcls"]
