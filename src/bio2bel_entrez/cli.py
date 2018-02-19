# -*- coding: utf-8 -*-

import logging

import click

from .constants import DEFAULT_CACHE_CONNECTION
from .manager import Manager


@click.group()
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
@click.pass_context
def main(ctx, connection):
    """Convert Entrez to BEL"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    ctx.obj = Manager(connection=connection)


default_tax_ids = [
    '9606',  # Human
    '10090',  # Mouse
    '10116',  # Rat
    '7227',  # Drosophila
    '4932',  # Yeast
]


@main.command()
@click.option('-t', '--tax-id', default=default_tax_ids, multiple=True,
              help='Keep this taxonomy identifier. Can specify multiple. Defaults to 9606 (human), 10090 (mouse), 10116'
                   ' (rat), 7227 (fly), and 4932 (yeast).')
@click.option('-a', '--all-tax-id', is_flag=True, help='Use all taxonomy identifiers')
@click.pass_obj
def populate(manager, tax_id, all_tax_id):
    """Populates the database"""
    if all_tax_id:
        tax_id_filter = None
    else:
        tax_id_filter = tax_id

    manager.populate(tax_id_filter=tax_id_filter)


@main.command()
@click.option('-y', '--yes', is_flag=True)
@click.pass_obj
def drop(manager, yes):
    """Drops database"""
    if yes or click.confirm('Drop everything?'):
        manager.drop_all()


@main.command()
@click.pass_obj
def summarize(manager):
    """Summarize the contents of the database"""
    click.echo('Genes: {}'.format(manager.count_genes()))
    click.echo('Species: {}'.format(manager.count_species()))
    click.echo('HomoloGenes: {}'.format(manager.count_homologenes()))


@main.group()
def gene():
    """Gene tools"""


@gene.command()
@click.argument('entrez_id')
@click.pass_obj
def get(manager, entrez_id):
    """Looks up a gene"""
    gene_model = manager.get_gene_by_entrez_id(entrez_id)

    if gene_model is None:
        click.echo('Unable to find gene: {}'.format(entrez_id))

    else:
        click.echo('Name: {}'.format(gene_model.name))
        click.echo('Description: {}'.format(gene_model.description))
        click.echo('Species: {}'.format(gene_model.species))

        if gene_model.homologene:
            click.echo('HomoloGene: {}'.format(gene_model.homologene))


@gene.command()
@click.option('-l', '--limit', type=int, default=10, help='Limit, defaults to 10.')
@click.option('-o', '--offset', type=int)
@click.pass_obj
def ls(manager, limit, offset):
    """List TSV of genes' identifiers, names, then species taxonomy identifiers"""
    for g in manager.list_genes(limit=limit, offset=offset):
        click.echo('\t'.join([g.entrez_id, g.name, str(g.species)]))


@main.group()
def species():
    """Species utils"""


@species.command()
@click.pass_obj
def ls(manager):
    """List species"""
    for s in manager.list_species():
        click.echo(s)


@main.command()
@click.option('-v', '--debug', is_flag=True)
@click.option('-h', '--host')
@click.option('-p', '--port', type=int)
@click.pass_obj
def web(manager, debug, port, host):
    """Run the admin interface"""
    from .web import get_app
    app = get_app(connection=manager, url='/')
    app.run(debug=debug, port=port, host=host)


if __name__ == '__main__':
    main()
