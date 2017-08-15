# -*- coding: utf-8 -*-

from flask import Flask
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from .download import Manager
from .models import Species, Gene


def get_app():
    """Builds a Flask application

    :rtype: flask.Flask
    """
    app = Flask(__name__)

    admin = Admin(app, template_mode='bootstrap3')

    manager = Manager()

    admin.add_view(ModelView(Species, manager.session))
    admin.add_view(ModelView(Gene, manager.session))

    return app


if __name__ == '__main__':
    app = get_app()
    app.run()
