
requires = ["requests",
            "requests_oauthlib"]
try:
    import argparse

except ImportError:
    requires.append('argparse')

try:
    from setuptools import setup
    kw = {
        "zip_safe": False,
        "install_requires": requires
    }
    setup  # silence pyflakes
except ImportError:
    from distutils.core import setup
    kw = {
        "requires": "requires"
    }

setup(name="pyopenphoto",
      version="0.1",
      description="OpenPhoto API client",
      author="Giacomo Bagnoli",
      author_email="gbagnoli@gmail.com",
      packages=["openphoto"],
      **kw
)



