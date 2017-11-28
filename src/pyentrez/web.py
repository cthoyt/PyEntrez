# -*- coding: utf-8 -*-

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from pyentrez.manager import Manager
from pyentrez.models import Gene, Species, Xref, Homologene


def add_admin(app, session, **kwargs):
    """Adds the administrator views

    :param flask.Flask app: A Flask application
    :param session:
    :param str url: The relative URL at which the admin app is plaed
    """
    admin = Admin(app, template_mode='bootstrap3', **kwargs)
    admin.add_view(ModelView(Gene, session))
    admin.add_view(ModelView(Xref, session))
    admin.add_view(ModelView(Species, session))
    admin.add_view(ModelView(Homologene, session))
    return admin


def create_application(connection=None, url=None):
    """Builds a Flask application

    :param Optional[str] connection:
    :param Optional[str] url:
    :rtype: flask.Flask
    """
    app = Flask(__name__)
    manager = Manager(connection=connection)
    add_admin(app, manager.session, url=url)
    return app


if __name__ == '__main__':
    create_application().run(debug=True, port=5000, host='0.0.0.0')
