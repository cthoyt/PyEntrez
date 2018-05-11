# -*- coding: utf-8 -*-

"""CLI for Bio2BEL Entrez."""

import click

from .manager import Manager

main = Manager.get_cli()


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


if __name__ == '__main__':
    main()
