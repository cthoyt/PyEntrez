# -*- coding: utf-8 -*-

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from .download import Manager
from .models import Species, Gene


def add_admin_views(app, session):
    """Adds the administrator views"""
    admin = Admin(app, template_mode='bootstrap3')
    admin.add_view(ModelView(Species, session))
    admin.add_view(ModelView(Gene, session))
    return admin


def get_app():
    """Builds a Flask application

    :rtype: flask.Flask
    """
    app = Flask(__name__)
    manager = Manager()
    add_admin_views(app, manager.session)
    return app


if __name__ == '__main__':
    get_app().run()
