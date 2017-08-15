# -*- coding: utf-8 -*-

import logging

import click

from .download import PopulateManager
from .web import get_app


@click.group()
def main():
    """PyEntrez"""
    logging.basicConfig(level=logging.INFO)


@main.command()
def populate():
    """Populates the database"""
    manager = PopulateManager()
    manager.populate()


@main.command()
def drop():
    """Drops database"""
    if click.confirm('Drop everything?'):
        manager = PopulateManager()
        manager.drop_tables()


@main.command()
def web():
    """Run the admin interface"""
    app = get_app()
    app.run()


if __name__ == '__main__':
    main()
