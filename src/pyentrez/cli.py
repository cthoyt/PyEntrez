# -*- coding: utf-8 -*-

import logging

import click

from .constants import DEFAULT_CACHE_CONNECTION
from .manager import Manager
from .web import get_app


@click.group()
def main():
    """Entrez to BEL"""
    logging.basicConfig(level=logging.INFO)


@main.command()
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
@click.option('-t', '--tax-id', help='Keep this taxonomy identifier. Can specify multiple', multiple=True)
def populate(connection, tax_id):
    """Populates the database"""
    m = Manager(connection=connection)
    m.populate(tax_id_filter=tax_id)


@main.command()
def drop():
    """Drops database"""
    if click.confirm('Drop everything?'):
        m = Manager()
        m.drop_all()


@main.command()
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
@click.option('-v', '--debug')
@click.option('-p', '--port')
@click.option('-h', '--host')
def web(connection, debug, port, host):
    """Run the admin interface"""
    app = get_app(connection=connection)
    app.run(debug=debug, port=port, host=host)


if __name__ == '__main__':
    main()
