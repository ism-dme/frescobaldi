# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2011 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

from __future__ import unicode_literals

"""
Some utility functions.
"""

import codecs
import contextlib
import os
import re

from PyQt4.QtGui import QColor

import variables


def iswritable(path):
    """Returns True if the path can be written to or created."""
    return ((os.path.exists(path) and os.access(path, os.W_OK))
            or os.access(os.path.dirname(path), os.W_OK))


def homify(path):
    """Replaces the homedirectory (if present) in the path with a tilde (~)."""
    homedir = os.path.expanduser('~')
    if path.startswith(homedir + os.sep):
        path = "~" + path[len(homedir):]
    return path


@contextlib.contextmanager
def signalsBlocked(*objs):
    """Blocks the signals of the given QObjects and then returns a contextmanager"""
    blocks = [obj.blockSignals(True) for obj in objs]
    try:
        yield
    finally:
        for obj, block in zip(objs, blocks):
            obj.blockSignals(block)


def addcolor(color, r, g, b):
    """Adds r, g and b values to the given color and returns a new QColor instance."""
    r += color.red()
    g += color.green()
    b += color.blue()
    d = max(r, g, b) - 255
    if d > 0:
        r = max(0, r - d)
        g = max(0, g - d)
        b = max(0, b - d)
    return QColor(r, g, b)


def mixcolor(color1, color2, mix):
    """Returns a QColor as if color1 is painted on color1 with alpha value mix (0.0 - 1.0)."""
    r1, g1, b1 = color1.red(), color1.green(), color1.blue()
    r2, g2, b2 = color2.red(), color2.green(), color2.blue()
    r = r1 * mix + r2 * (1 - mix)
    g = g1 * mix + g2 * (1 - mix)
    b = b1 * mix + b2 * (1 - mix)
    return QColor(r, g, b)


def naturalsort(text):
    """Returns a key for the list.sort() method.
    
    Intended to sort strings in a human way, for e.g. version numbers.
    
    """
    return tuple(int(s) if s.isdigit() else s for s in re.split(r'(\d+)', text))


def uniq(iterable):
    """Returns an iterable, removing duplicates. The items should be hashable."""
    s, l = set(), 0
    for i in iterable:
        s.add(i)
        if len(s) > l:
            yield i
            l = len(s)


def decode(data, encoding=None):
    """Returns the unicode text from the encoded, data. Prefer encoding if given.
    
    The text is also checked for the 'coding' document variable.
    
    """
    encodings = [encoding] if encoding else []
    for bom, encoding in (
        (codecs.BOM_UTF8, 'utf-8'),
        (codecs.BOM_UTF16_LE, 'utf_16_le'),
        (codecs.BOM_UTF16_BE, 'utf_16_be'),
            ):
        if data.startswith(bom):
            encodings.append(encoding)
            data = data[len(bom):]
            break
    else:
        var_coding = variables.variables(data).get("coding")
        if var_coding:
            encodings.append(var_coding)
    encodings.append('utf-8')
    encodings.append('latin1')
    
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except (UnicodeError, LookupError):
            continue
    return data.decode('utf-8', 'replace')


def encode(text, default_encoding='utf-8'):
    """Returns the bytes representing the text, encoded.
    
    Looks at the 'coding' variable to determine the encoding,
    otherwise falls back to the given default encoding, defaulting to 'utf-8'.
    
    """
    encoding = variables.variables(text).get("coding")
    if encoding:
        try:
            return text.encode(encoding)
        except (LookupError, UnicodeError):
            pass
    return text.encode(default_encoding)


