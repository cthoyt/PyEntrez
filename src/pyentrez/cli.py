# -*- coding: utf-8 -*-

import logging

import click

from .constants import DEFAULT_CACHE_CONNECTION
from .manager import Manager


@click.group()
def main():
    """Entrez to BEL"""
    logging.basicConfig(level=logging.INFO)


@main.command()
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
@click.option('-t', '--tax-id', default=['9606'], multiple=True,
              help='Keep this taxonomy identifier. Can specify multiple. Defaults to just human')
def populate(connection, tax_id):
    """Populates the database"""
    m = Manager(connection=connection)
    m.populate(tax_id_filter=tax_id)


@main.command()
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
def drop(connection):
    """Drops database"""
    if click.confirm('Drop everything?'):
        m = Manager(connection=connection)
        m.drop_all()


@main.command()
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
@click.option('-v', '--debug', is_flag=True)
@click.option('-p', '--port')
@click.option('-h', '--host')
def web(connection, debug, port, host):
    """Run the admin interface"""
    from .web import create_application
    app = create_application(connection=connection, url='/')
    app.run(debug=debug, port=port, host=host)


if __name__ == '__main__':
    main()
