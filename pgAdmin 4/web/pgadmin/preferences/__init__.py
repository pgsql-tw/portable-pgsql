##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2020, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""
Implements the routes for creating Preferences/Options Dialog on the client
side and for getting/setting preferences.
"""

import config
import simplejson as json
from flask import render_template, url_for, Response, request, session
from flask_babelex import gettext
from flask_security import login_required
from pgadmin.utils import PgAdminModule
from pgadmin.utils.ajax import success_return, \
    make_response as ajax_response, internal_server_error
from pgadmin.utils.menu import MenuItem
from pgadmin.utils.preferences import Preferences

MODULE_NAME = 'preferences'


class PreferencesModule(PgAdminModule):
    """
    PreferenceModule represets the preferences of different modules to the
    user in UI.

    And, allows the user to modify (not add/remove) as per their requirement.
    """

    def get_own_javascripts(self):
        return [{
            'name': 'pgadmin.preferences',
            'path': url_for('preferences.index') + 'preferences',
            'when': None
        }]

    def get_own_stylesheets(self):
        return []

    def get_own_menuitems(self):
        return {
            'file_items': [
                MenuItem(name='mnu_preferences',
                         priority=997,
                         module="pgAdmin.Preferences",
                         callback='show',
                         icon='fa fa-cog',
                         label=gettext('Preferences'))
            ]
        }

    def get_exposed_url_endpoints(self):
        """
        Returns:
            list: a list of url endpoints exposed to the client.
        """
        return [
            'preferences.index',
            'preferences.get_by_name',
            'preferences.get_all'
        ]


blueprint = PreferencesModule(MODULE_NAME, __name__)


@blueprint.route("/preferences.js")
@login_required
def script():
    """render the required javascript"""
    return Response(
        response=render_template("preferences/preferences.js", _=gettext),
        status=200,
        mimetype="application/javascript"
    )


@blueprint.route("/", methods=["GET"], endpoint='index')
@blueprint.route("/<module>/<preference>", endpoint='get_by_name')
@login_required
def preferences(module=None, preference=None):
    """Fetch all/or requested preferences of pgAdmin IV."""

    if module is not None and preference is not None:
        try:
            m = Preferences.module(module, create=False)
            if m is None:
                return Response(status=404)

            p = m.preference(preference)
            if p is None:
                return Response(status=404)

            return ajax_response(
                response=p.to_json(),
                status=200
            )

        except Exception as e:
            return internal_server_error(errormsg=str(e))

    # Load Preferences
    pref = Preferences.preferences()
    res = []

    def label(p):
        return gettext(p['label'])

    for m in pref:
        if len(m['categories']):
            om = {
                "id": m['id'],
                "label": gettext(m['label']),
                "inode": True,
                "open": True,
                "branch": []
            }

            for c in m['categories']:
                for p in c['preferences']:
                    if 'label' in p and p['label'] is not None:
                        p['label'] = gettext(p['label'])
                    if 'help_str' in p and p['help_str'] is not None:
                        p['help_str'] = gettext(p['help_str'])
                oc = {
                    "id": c['id'],
                    "mid": m['id'],
                    "label": gettext(c['label']),
                    "inode": False,
                    "open": False,
                    "preferences": sorted(c['preferences'], key=label)
                }

                (om['branch']).append(oc)
            om['branch'] = sorted(om['branch'], key=label)

            res.append(om)

    return ajax_response(
        response=sorted(res, key=label),
        status=200
    )


@blueprint.route("/get_all", methods=["GET"], endpoint='get_all')
@login_required
def preferences_s():
    """Fetch all preferences for caching."""
    # Load Preferences
    pref = Preferences.preferences()
    res = []

    for m in pref:
        if len(m['categories']):
            for c in m['categories']:
                for p in c['preferences']:
                    p['module'] = m['name']
                    res.append(p)

    return ajax_response(
        response=res,
        status=200
    )


@blueprint.route("/<int:pid>", methods=["PUT"], endpoint="update")
@login_required
def save(pid):
    """
    Save a specific preference.
    """
    data = request.form if request.form else json.loads(request.data.decode())

    res, msg = Preferences.save(
        data['mid'], data['category_id'], data['id'], data['value'])

    if not res:
        return internal_server_error(errormsg=msg)

    response = success_return()

    # Set cookie & session for language settings.
    # This will execute every time as could not find the better way to know
    # that which preference is getting updated.

    misc_preference = Preferences.module('misc')
    user_languages = misc_preference.preference(
        'user_language'
    )

    language = 'en'
    if user_languages:
        language = user_languages.get() or language

    domain = dict()
    if config.COOKIE_DEFAULT_DOMAIN and\
            config.COOKIE_DEFAULT_DOMAIN != 'localhost':
        domain['domain'] = config.COOKIE_DEFAULT_DOMAIN

    setattr(session, 'PGADMIN_LANGUAGE', language)
    response.set_cookie("PGADMIN_LANGUAGE", value=language,
                        path=config.COOKIE_DEFAULT_PATH,
                        **domain)

    return response
