##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2020, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
#########################################################################

"""Utilities for HTML"""

from pgadmin.utils import IS_PY2

if IS_PY2:
    from cgi import escape as html_escape
else:
    from html import escape as html_escape


def safe_str(x):
    try:
        # For Python2, it can be int, long, float
        if IS_PY2:
            if isinstance(x, (int, long, float)):
                x = str(x)
        else:
            # For Python3, it can be int, float
            if isinstance(x, (int, float)):
                x = str(x)

        x = x.encode(
            'ascii', 'xmlcharrefreplace'
        ) if hasattr(x, 'encode') else x

        if not IS_PY2:
            x = x.decode('utf-8')
    except Exception:
        pass
    return html_escape(x, False)
