# -*- coding: utf-8 -*-

import sys

import click

from .constants import default_tax_ids

__all__ = [
    'add_populate_to_cli',
]


def add_populate_to_cli(main):
    @main.command()
    @click.option('--reset', is_flag=True, help='Nuke database first')
    @click.option('--force', is_flag=True, help='Force overwrite if already populated')
    @click.option('-t', '--tax-id', default=default_tax_ids, multiple=True,
                  help='Keep this taxonomy identifier. Can specify multiple. Defaults to 9606 (human), 10090 (mouse), 10116'
                       ' (rat), 7227 (fly), and 4932 (yeast).')
    @click.option('-a', '--all-tax-id', is_flag=True, help='Use all taxonomy identifiers')
    @click.pass_obj
    def populate(manager, reset, force, tax_id, all_tax_id):
        """Populates the database"""
        if all_tax_id:
            tax_id_filter = None
        else:
            tax_id_filter = tax_id

        if reset:
            click.echo('Deleting the previous instance of the database')
            manager.drop_all()
            click.echo('Creating new models')
            manager.create_all()

        if manager.is_populated() and not force:
            click.echo('Database already populated. Use --force to overwrite')
            sys.exit(0)

        manager.populate(tax_id_filter=tax_id_filter)

    return main
