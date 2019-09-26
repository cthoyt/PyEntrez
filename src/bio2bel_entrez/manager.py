# -*- coding: utf-8 -*-

"""Manager for Bio2BEL Entrez."""

import logging
import sys
import time
from typing import Dict, Iterable, List, Optional, Tuple

import click
from bio2bel import AbstractManager
from bio2bel.manager.flask_manager import FlaskMixin
from bio2bel.manager.namespace_manager import BELNamespaceManagerMixin
from networkx import relabel_nodes
from pybel import BELGraph
from pybel.constants import FUNCTION, NAMESPACE
from pybel.dsl import BaseEntity
from pybel.manager.models import Namespace, NamespaceEntry
from sqlalchemy import and_
from tqdm import tqdm

from .constants import DEFAULT_TAX_IDS, MODULE_NAME, VALID_ENTREZ_NAMESPACES, VALID_MGI_NAMESPACES
from .homologene_manager import Manager as HomologeneManager
from .models import Base, Gene, Homologene, Species, Xref
from .parser import get_gene_info_df, get_homologene_df

__all__ = [
    'Manager',
]

log = logging.getLogger(__name__)


class Manager(AbstractManager, BELNamespaceManagerMixin, FlaskMixin):
    """Genes and orthologies."""

    module_name = MODULE_NAME
    _base = Base
    flask_admin_models = [Gene, Homologene, Species, Xref]

    namespace_model = Gene
    identifiers_recommended = 'NCBI Gene'
    identifiers_pattern = r'^\d+$'
    identifiers_miriam = 'MIR:00000069'
    identifiers_namespace = 'ncbigene'
    identifiers_url = 'http://identifiers.org/ncbigene/'

    def __init__(self, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)

        self.species_cache = {}
        self.gene_cache = {}
        self.homologene_cache = {}
        self.gene_homologene = {}

    def is_populated(self) -> bool:
        """Check if the database is already populated."""
        return 0 < self.count_genes()

    @staticmethod
    def _get_identifier(gene: Gene) -> str:
        return gene.entrez_id

    def _create_namespace_entry_from_model(self, gene: Gene, namespace: Namespace) -> NamespaceEntry:
        return NamespaceEntry(
            encoding=gene.bel_encoding,
            name=gene.name,
            identifier=gene.entrez_id,
            namespace=namespace,
        )

    def get_or_create_species(self, taxonomy_id: str, **kwargs) -> Species:
        """Get or create a Species model.

        :param taxonomy_id: NCBI taxonomy identifier
        """
        species = self.species_cache.get(taxonomy_id)

        if species is not None:
            self.session.add(species)
            return species

        species = self.session.query(Species).filter(Species.taxonomy_id == taxonomy_id).one_or_none()

        if species is None:
            species = self.species_cache[taxonomy_id] = Species(taxonomy_id=taxonomy_id, **kwargs)
            self.session.add(species)

        return species

    def get_gene_by_entrez_id(self, entrez_id: str) -> Optional[Gene]:
        """Get a gene with the given Entrez Gene identifier, if it exists.

        :param entrez_id: Entrez Gene identifier
        """
        return self.session.query(Gene).filter(Gene.entrez_id == entrez_id).one_or_none()

    def get_genes_by_name(self, name: str) -> List[Gene]:
        """Get a list of genes with the given name (case insensitive).

        :param name: A gene name
        """
        return self.session.query(Gene).filter(Gene.name.lower() == name.lower()).all()

    def get_gene_by_rgd_name(self, name: str) -> Optional[Gene]:
        """Get a gene by its RGD name.

        :param name: RGD gene symbol
        """
        rgd_name_filter = and_(Species.taxonomy_id == '10116', Gene.name == name)
        rv = self.session.query(Gene).join(Species).filter(rgd_name_filter).all()
        return self._return_lowest(name, rv)

    @staticmethod
    def _return_lowest(name, rv):
        if len(rv) == 0:
            return

        if len(rv) == 1:
            return rv[0]

        rv = sorted(rv, key=lambda gene: int(gene.entrez_id))

        log.warning('Found multiple rows for Entrez Gene named %s. Returning lowest Entrez Gene identifier of:\n%s',
                    name, '\n'.join(map(str, rv)))

        return rv[0]

    def get_gene_by_mgi_name(self, name: str) -> Optional[Gene]:
        """Get a gene by its MGI name.

        :param name: MGI gene symbol
        """
        mgi_name_filter = and_(Species.taxonomy_id == '10090', Gene.name == name)
        rv = self.session.query(Gene).join(Species).filter(mgi_name_filter).all()
        return self._return_lowest(name, rv)

    def get_gene_by_hgnc_name(self, name: str) -> Optional[Gene]:
        """Get a gene by its HGNC gene symbol."""
        hgnc_name_filter = and_(Species.taxonomy_id == '9606', Gene.name == name)
        rv = self.session.query(Gene).join(Species).filter(hgnc_name_filter).all()
        return self._return_lowest(name, rv)

    def get_or_create_gene(self, entrez_id: str, **kwargs) -> Gene:
        """Get or create a Gene model.

        :param entrez_id: Entrez Gene identifier
        """
        gene = self.gene_cache.get(entrez_id)

        if gene is not None:
            self.session.add(gene)
            return gene

        gene = self.get_gene_by_entrez_id(entrez_id)

        if gene is None:
            gene = self.gene_cache[entrez_id] = Gene(entrez_id=entrez_id, **kwargs)
            self.session.add(gene)

        return gene

    def get_or_create_homologene(self, homologene_id: str, **kwargs) -> Homologene:
        """Get or create a HomoloGene model.

        :param homologene_id: HomoloGene Gene identifier
        """
        homologene = self.homologene_cache.get(homologene_id)

        if homologene is not None:
            self.session.add(homologene)
            return homologene

        homologene = self.session.query(Homologene).filter(Homologene.homologene_id == homologene_id).one_or_none()

        if homologene is None:
            homologene = self.homologene_cache[homologene_id] = Homologene(homologene_id=homologene_id, **kwargs)
            self.session.add(homologene)

        return homologene

    def populate_homologene(self, url=None, cache=True, force_download=False, tax_id_filter=None) -> None:
        """Populate the database.

        :param Optional[str] url: Homologene data url
        :param bool cache: If true, the data is downloaded to the file system, else it is loaded from the internet
        :param bool force_download: If true, overwrites a previously cached file
        :param Optional[iter[str]] tax_id_filter: Species to keep
        """
        df = get_homologene_df(url=url, cache=cache, force_download=force_download)

        if tax_id_filter is not None:
            tax_id_filter = set(tax_id_filter)
            log.info('filtering HomoloGene to %s', tax_id_filter)
            df = df[df['tax_id'].isin(tax_id_filter)]

        log.info('preparing HomoloGene models')

        grouped_df = df.groupby('homologene_id')
        for homologene_id, sub_df in tqdm(grouped_df, desc='HomoloGene', total=len(grouped_df)):

            homologene = Homologene(homologene_id=homologene_id)
            self.session.add(homologene)

            for _, (homologene_id, taxonomy_id, entrez_id, name, _, _) in sub_df.iterrows():
                entrez_id = str(int(entrez_id))
                self.gene_homologene[entrez_id] = homologene

        t = time.time()
        log.info('committing HomoloGene models')
        self.session.commit()
        log.info('committed HomoloGene models in %.2f seconds', time.time() - t)

    def populate_gene_info(self,
                           url: Optional[str] = None,
                           cache: bool = True,
                           force_download: bool = False,
                           interval: Optional[int] = None,
                           tax_id_filter: Iterable[str] = None):
        """Populate the database.

        :param url: A custom url to download
        :param interval: The number of records to commit at a time
        :param cache: If true, the data is downloaded to the file system, else it is loaded from the internet
        :param force_download: If true, overwrites a previously cached file
        :param tax_id_filter: Species to keep
        """
        df = get_gene_info_df(url=url, cache=cache, force_download=force_download)

        if tax_id_filter is not None:
            tax_id_filter = set(tax_id_filter)
            log.info('filtering Entrez Gene to %s', tax_id_filter)
            df = df[df['#tax_id'].isin(tax_id_filter)]

        log.info('preparing Entrez Gene models')
        for taxonomy_id, sub_df in tqdm(df.groupby('#tax_id'), desc='Species'):
            taxonomy_id = str(int(taxonomy_id))
            species = self.get_or_create_species(taxonomy_id=taxonomy_id)

            species_it = tqdm(sub_df.itertuples(), desc='Tax ID {}'.format(taxonomy_id), total=len(sub_df.index),
                              leave=False)
            for idx, _, entrez_id, name, xrefs, description, type_of_gene in species_it:
                entrez_id = str(int(entrez_id))

                if isinstance(name, float):
                    log.debug('Missing name: %s %s', entrez_id, description)
                    # These errors are due to placeholder entries for GeneRIFs and only occur once per species
                    continue

                gene = Gene(
                    entrez_id=entrez_id,
                    species=species,
                    name=name,
                    description=description,
                    type_of_gene=type_of_gene,
                    homologene=self.gene_homologene.get(entrez_id)
                )
                self.session.add(gene)

                if not isinstance(xrefs, float):
                    for xref in xrefs.split('|'):
                        database, value = xref.split(':', 1)
                        gene.xrefs.append(Xref(database=database, value=value))

                if interval and idx % interval == 0:
                    self.session.commit()

        log.info('committing Entrez Gene models')
        self.session.commit()

    def populate(self,
                 gene_info_url: Optional[str] = None,
                 interval: Optional[int] = None,
                 tax_id_filter: Iterable[str] = DEFAULT_TAX_IDS,
                 homologene_url: Optional[str] = None):
        """Populate the database.

        :param gene_info_url: A custom url to download
        :param interval: The number of records to commit at a time
        :param tax_id_filter: Species to keep. Defaults to 9606 (human), 10090 (mouse), 10116
         (rat), 7227 (fly), and 4932 (yeast). Explicitly set to None to get all taxonomies.
        :param homologene_url: A custom url to download
        """
        self.populate_homologene(url=homologene_url, tax_id_filter=tax_id_filter)
        self.populate_gene_info(url=gene_info_url, interval=interval, tax_id_filter=tax_id_filter)

    def _handle_entrez_node(self, identifier=None, name=None):
        if identifier:
            return self.get_gene_by_entrez_id(identifier)
        elif name:
            return self.get_gene_by_entrez_id(name)
        else:
            raise IndexError

    def _handle_hgnc_node(self, identifier=None, name=None) -> Optional[Gene]:
        if name:
            return self.get_gene_by_hgnc_name(name)

    def _handle_rgd_node(self, identifier=None, name=None) -> Optional[Gene]:
        if name:
            return self.get_gene_by_rgd_name(name)

    def _handle_mgi_node(self, identifier=None, name=None) -> Optional[Gene]:
        if name:
            return self.get_gene_by_mgi_name(name)

    def lookup_node(self, node: BaseEntity) -> Optional[Gene]:
        """Look up a gene from a PyBEL data dictionary."""
        namespace = node.get(NAMESPACE)
        if namespace is None:
            return

        name = node.name
        identifier = node.identifier

        if namespace.lower() in VALID_ENTREZ_NAMESPACES:
            return self._handle_entrez_node(identifier, name)

        # if namespace.lower() == 'hgnc':
        #     return self._handle_hgnc_node(identifier, name)
        #
        # if namespace.lower() in VALID_MGI_NAMESPACES:
        #     return self._handle_mgi_node(identifier, name)
        #
        # if namespace.lower() == 'rgd':
        #     return self._handle_rgd_node(identifier, name)

    def iter_genes(self, graph: BELGraph, use_tqdm: bool = False) -> Iterable[Tuple[BaseEntity, Gene]]:
        """Iterate over genes in the graph that can be mapped to an Entrez gene."""
        it = (
            tqdm(graph, desc='Entrez genes')
            if use_tqdm else
            graph
        )
        for node in it:
            gene_model = self.lookup_node(node)
            if gene_model is not None:
                yield node, gene_model

    def normalize_genes(self, graph: BELGraph, use_tqdm: bool = False) -> None:
        """Add identifiers to all Entrez genes."""
        mapping = {
            node: gene_model.as_bel(func=node.function)
            for node, gene_model in self.iter_genes(graph, use_tqdm=use_tqdm)
        }
        relabel_nodes(graph, mapping, copy=False)

    def enrich_genes_with_homologenes(self, graph: BELGraph) -> None:
        """Enrich the nodes in a graph with their HomoloGene parents."""
        self.add_namespace_to_graph(graph)
        self.add_homologene_namespace_to_graph(graph)

        for node_data, gene_model in self.iter_genes(graph):
            homologene = gene_model.homologene
            if homologene is None:
                continue
            graph.add_is_a(node_data, homologene.as_bel(node_data[FUNCTION]))

    def enrich_equivalences(self, graph: BELGraph) -> None:
        """Add equivalent node information."""
        self.add_namespace_to_graph(graph)

        for node, gene_model in list(self.iter_genes(graph)):
            graph.add_equivalence(node, gene_model.as_bel(node[FUNCTION]))

    def enrich_orthologies(self, graph: BELGraph) -> None:
        """Add ortholog relationships to graph."""
        self.add_namespace_to_graph(graph)
        self.add_homologene_namespace_to_graph(graph)

        for node, gene_model in list(self.iter_genes(graph)):
            if not gene_model.homologene:
                continue  # sad gene doesn't have any friends :/

            for ortholog in gene_model.homologene.genes:
                ortholog_node = ortholog.as_bel(node[FUNCTION])
                if ortholog_node == node:
                    continue
                graph.add_orthology(node, ortholog_node)

    def add_homologene_namespace_to_graph(self, graph: BELGraph) -> Namespace:
        """Add the homologene namespace to the graph."""
        homologene_manager = HomologeneManager(engine=self.engine, session=self.session)
        return homologene_manager.add_namespace_to_graph(graph)

    def count_genes(self) -> int:
        """Count the genes in the database."""
        return self._count_model(Gene)

    def count_homologenes(self) -> int:
        """Count the HomoloGenes in the database."""
        return self._count_model(Homologene)

    def count_species(self) -> int:
        """Count the species in the database."""
        return self._count_model(Species)

    def list_species(self) -> List[Species]:
        """List all species in the database."""
        return self._list_model(Species)

    def list_homologenes(self) -> List[Homologene]:
        """List all HomoloGenes in the database."""
        return self._list_model(Homologene)

    def summarize(self) -> Dict[str, int]:
        """Return a summary dictionary over the content of the database."""
        return dict(
            genes=self.count_genes(),
            species=self.count_species(),
            homologenes=self.count_homologenes()
        )

    def list_genes(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Gene]:
        """List genes in the database."""
        query = self.session.query(Gene)
        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        return query.all()

    @staticmethod
    def _cli_add_populate(main: click.Group) -> click.Group:
        """Overwrite the populate method since it needs to check tax identifiers."""
        return add_populate_to_cli(main)


def add_populate_to_cli(main: click.Group) -> click.Group:  # noqa: D202
    """Add a custom population function to the command line interface."""

    @main.command()
    @click.option('--reset', is_flag=True, help='Nuke database first')
    @click.option('--force', is_flag=True, help='Force overwrite if already populated')
    @click.option('-t', '--tax-id', multiple=True,
                  help='Keep this taxonomy identifier. Can specify multiple. Defaults to 9606 (human), 10090 (mouse), '
                       '10116 (rat), 7227 (fly), and 4932 (yeast).')
    @click.option('-a', '--all-tax-id', is_flag=True, help='Use all taxonomy identifiers')
    @click.pass_obj
    def populate(manager, reset, force, tax_id, all_tax_id):
        """Populate the database."""
        if all_tax_id:
            tax_id_filter = None
        elif not tax_id:
            tax_id_filter = DEFAULT_TAX_IDS
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
