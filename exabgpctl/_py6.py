# -*- coding: utf-8 -*-
"""
exabgpctl._py6
~~~~~~~~~~~~~~

Main hacks of this file came from six module
    https://github.com/benjaminp/six/blob/master/six.py
    six is under license MIT

And https://github.com/ahmet2mir/python-artron/blob/master/artron/_py6.py
"""
import sys

PY2 = sys.version_info[0] == 2

# pylint: disable=invalid-name,redefined-builtin,undefined-variable

if PY2:
    text_type = unicode
    string_types = (str, unicode)

    iterkeys = lambda x: x.iterkeys()
    itervalues = lambda x: x.itervalues()
    iteritems = lambda x: x.iteritems()
else:
    text_type = str
    string_types = (str,)

    iterkeys = lambda x: iter(x.keys())
    itervalues = lambda x: iter(x.values())
    iteritems = lambda x: iter(x.items())
