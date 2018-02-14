# -*- coding: utf-8 -*-

import click
import logging

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
def summarize(connection):
    """Summarize the contents of the database"""
    m = Manager(connection=connection)

    click.echo('Genes: {}'.format(m.count_genes()))
    click.echo('Species: {}'.format(m.count_species()))
    click.echo('HomoloGenes: {}'.format(m.count_homologenes()))


@main.group()
def gene():
    pass


@gene.command()
@click.argument('entrez_id')
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
def get(connection, entrez_id):
    """Looks up a gene by its identifier and prints a summary"""
    m = Manager(connection=connection)
    gene = m.get_gene_by_entrez_id(entrez_id)

    if gene is None:
        click.echo('Unable to find gene: {}'.format(entrez_id))

    else:
        click.echo('Name: {}'.format(gene.name))
        click.echo('Description: {}'.format(gene.description))
        click.echo('Species: {}'.format(gene.species))

        if gene.homologene:
            click.echo('HomoloGene: {}'.format(gene.homologene))


@gene.command()
@click.option('-c', '--connection', help='Defaults to {}'.format(DEFAULT_CACHE_CONNECTION))
@click.option('-l', '--limit', type=int, default=10)
@click.option('-o', '--offset', type=int)
def ls(connection, limit, offset):
    m = Manager(connection=connection)

    for gene in m.list_genes(limit=limit, offset=offset):
        click.echo('\t'.join([gene.entrez_id, gene.name, str(gene.species)]))


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
