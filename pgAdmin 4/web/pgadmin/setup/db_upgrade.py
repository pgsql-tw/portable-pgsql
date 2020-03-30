##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2020, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

import os
import flask_migrate

from pgadmin import db


def db_upgrade(app):
    from pgadmin.utils import u, fs_encoding
    with app.app_context():
        flask_migrate.Migrate(app, db)
        migration_folder = os.path.join(
            os.path.dirname(os.path.realpath(u(__file__, fs_encoding))),
            os.pardir, os.pardir,
            u'migrations'
        )
        flask_migrate.upgrade(migration_folder)
