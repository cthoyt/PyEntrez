# -*- coding: utf-8 -*-

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from pyentrez.manager import Manager
from pyentrez.models import Gene, Species, Xref


def add_admin_views(app, session, url='/'):
    """Adds the administrator views

    :param flask.Flask app: A Flask application
    :param session:
    :param str url: The relative URL at which the admin app is plaed
    """
    admin = Admin(app, url=url, template_mode='bootstrap3')
    admin.add_view(ModelView(Gene, session))
    admin.add_view(ModelView(Xref, session))
    admin.add_view(ModelView(Species, session))
    return admin


def get_app(connection=None):
    """Builds a Flask application

    :rtype: flask.Flask
    """
    app = Flask(__name__)
    manager = Manager(connection=connection)
    add_admin_views(app, manager.session)
    return app


if __name__ == '__main__':
    get_app().run(debug=True, port=5000, host='0.0.0.0')
