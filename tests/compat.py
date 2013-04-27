#!/usr/bin/env python
try:
    import unittest2 as unittest
    unittest  # silence pyflakes

except ImportError:
    import unittest

try:
    import mock
    mock  # silence pyflakes
except ImportError:
    import unittest.mock as mock


__all__ = ["mock", "unittest"]
