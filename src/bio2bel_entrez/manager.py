# -*- coding: utf-8 -*-

"""Manager for Bio2BEL Entrez."""

import logging
import sys
import time

from bio2bel import AbstractManager
from bio2bel.manager.flask_manager import FlaskMixin
from bio2bel.manager.namespace_manager import BELNamespaceManagerMixin
import click
from pybel.constants import FUNCTION, GENE, IDENTIFIER, NAME, NAMESPACE
from pybel.manager.models import NamespaceEntry
from sqlalchemy import and_
from tqdm import tqdm

from .constants import DEFAULT_TAX_IDS, MODULE_NAME
from .models import Base, Gene, Homologene, Species, Xref
from .parser import get_entrez_df, get_homologene_df

__all__ = [
    'SPECIES_CONSORTIUM_MAPPING',
    'CONSORTIUM_SPECIES_MAPPING',
    'Manager',
]

log = logging.getLogger(__name__)

SPECIES_CONSORTIUM_MAPPING = {
    '10090': 'MGI',
    '10116': 'RGD',
    '4932': 'SGD',
    '7227': 'FLYBASE',
    '9606': 'HGNC',
}

#: All namepace codes (in lowercase) that can map to ncbigene
VALID_ENTREZ_NAMESPACES = {'egid', 'eg', 'entrez', 'ncbigene'}
VALID_MGI_NAMESPACES = {'mgi', 'mgd'}

CONSORTIUM_SPECIES_MAPPING = {
    database_code: taxonomy_id
    for taxonomy_id, database_code in SPECIES_CONSORTIUM_MAPPING.items()
}


class Manager(AbstractManager, BELNamespaceManagerMixin, FlaskMixin):
    """Manages the Entrez Gene database."""

    module_name = MODULE_NAME
    flask_admin_models = [Gene, Homologene, Species, Xref]
    namespace_model = Gene

    identifiers_recommended = 'NCBI Gene'
    identifiers_pattern = '^\d+$'
    identifiers_miriam = 'MIR:00000069'
    identifiers_namespace = 'ncbigene'
    identifiers_url = 'http://identifiers.org/ncbigene/'

    def __init__(self, *args, **kwargs):  # noqa: D107
        super().__init__(*args, **kwargs)

        self.species_cache = {}
        self.gene_cache = {}
        self.homologene_cache = {}
        self.gene_homologene = {}

    @property
    def _base(self):
        return Base

    def is_populated(self):
        """Check if the database is already populated.

        :rtype: bool
        """
        return 0 < self.count_genes()

    @staticmethod
    def _get_identifier(model) -> str:
        return model.entrez_id

    def _create_namespace_entry_from_model(self, model, namespace) -> NamespaceEntry:
        return NamespaceEntry(
            encoding='G',
            name=model.name,
            identifier=model.entrez_id,
            namespace=namespace,
        )

    def get_or_create_species(self, taxonomy_id, **kwargs):
        """Get or create a Species model.

        :param str taxonomy_id: NCBI taxonomy identifier
        :rtype: Gene
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

    def get_gene_by_entrez_id(self, entrez_id):
        """Get a gene with the given Entrez Gene identifier.

        :param str entrez_id: Entrez Gene identifier
        :rtype: Optional[Gene]
        """
        return self.session.query(Gene).filter(Gene.entrez_id == entrez_id).one_or_none()

    def get_genes_by_name(self, name):
        """Get a list of genes with the given name (case insensitive).

        :param str name: A gene name
        :rtype: list[Gene]
        """
        return self.session.query(Gene).filter(Gene.name.lower() == name.lower()).all()

    def get_gene_by_rgd_name(self, name):
        """Get a gene by its RGD name.

        :param str name: RGD gene symbol
        :rtype: Optional[Gene]
        """
        rgd_name_filter = and_(Species.taxonomy_id == '10116', Gene.name == name)
        return self.session.query(Gene).join(Species).filter(rgd_name_filter).one_or_none()

    def get_gene_by_mgi_name(self, name):
        """Get a gene by its MGI name.

        :param str name: MGI gene symbol
        :rtype: Optional[Gene]
        """
        mgi_name_filter = and_(Species.taxonomy_id == '10090', Gene.name == name)
        return self.session.query(Gene).join(Species).filter(mgi_name_filter).one_or_none()

    def get_gene_by_hgnc_name(self, name):
        """Get a gene by its HGNC gene symbol.

        :param str name: HGNC gene symbol
        :rtype: Optional[Gene]
        """
        hgnc_name_filter = and_(Species.taxonomy_id == '9606', Gene.name == name)
        return self.session.query(Gene).join(Species).filter(hgnc_name_filter).one_or_none()

    def get_or_create_gene(self, entrez_id, **kwargs):
        """Get or create a Gene model.

        :param str entrez_id: Entrez Gene identifier
        :rtype: Gene
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

    def get_or_create_homologene(self, homologene_id, **kwargs):
        """Get or create a HomoloGene model.

        :param str homologene_id: HomoloGene Gene identifier
        :rtype: Homologene
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

    def populate_homologene(self, url=None, cache=True, force_download=False, tax_id_filter=None):
        """Populate the database.

        :param Optional[str] url: Homologene data url
        :param bool cache: If true, the data is downloaded to the file system, else it is loaded from the internet
        :param bool force_download: If true, overwrites a previously cached file
        :param Optional[set[str]] tax_id_filter: Species to keep
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

    def populate_gene_info(self, url=None, cache=True, force_download=False, interval=None, tax_id_filter=None):
        """Populate the database.

        :param Optional[str] url: A custom url to download
        :param Optional[int] interval: The number of records to commit at a time
        :param bool cache: If true, the data is downloaded to the file system, else it is loaded from the internet
        :param bool force_download: If true, overwrites a previously cached file
        :param Optional[set[str]] tax_id_filter: Species to keep
        """
        df = get_entrez_df(url=url, cache=cache, force_download=force_download)

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

    def populate(self, gene_info_url=None, interval=None, tax_id_filter=None, homologene_url=None):
        """Populate the database.

        :param Optional[str] gene_info_url: A custom url to download
        :param Optional[int] interval: The number of records to commit at a time
        :param Optional[set[str]] tax_id_filter: Species to keep
        :param Optional[str] homologene_url: A custom url to download
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

    def _handle_hgnc_node(self, identifier=None, name=None):
        if name:
            return self.get_gene_by_hgnc_name(name)

    def _handle_rgd_node(self, identifier=None, name=None):
        if name:
            return self.get_gene_by_rgd_name(name)

    def _handle_mgi_node(self, identifier=None, name=None):
        if name:
            return self.get_gene_by_mgi_name(name)

    def lookup_node(self, data):
        """Look up a gene from a PyBEL data dictionary.

        :param dict data: A PyBEL data dictionary
        :rtype: Optional[Gene]
        """
        if data[FUNCTION] != GENE:
            return

        namespace = data.get(NAMESPACE)

        if namespace is None:
            return

        name = data.get(NAME)
        identifier = data.get(IDENTIFIER)

        if namespace.lower() in VALID_ENTREZ_NAMESPACES:
            return self._handle_entrez_node(identifier, name)

        if namespace.lower() == 'hgnc':
            return self._handle_hgnc_node(identifier, name)

        if namespace.lower() in VALID_MGI_NAMESPACES:
            return self._handle_mgi_node(identifier, name)

        if namespace.lower() == 'rgd':
            return self._handle_rgd_node(identifier, name)

    def _iter_gene_data(self, graph):
        """Iterate over genes in the graph that can be mapped to an Entrez gene.

        :param pybel.BELGraph graph:
        :rtype: iter[tuple[tuple,dict,Gene]]
        """
        for gene_node, data in graph.nodes(data=True):
            gene = self.lookup_node(data)

            if gene is None:
                continue

            yield gene_node, data, gene

    def enrich_genes_with_homologenes(self, graph):
        """Enrich the nodes in a graph with their HomoloGene parents.

        :type graph: pybel.BELGraph
        """
        for gene_node, data, gene in self._iter_gene_data(graph):
            homologene_node = graph.add_node_from_data(gene.homologene.as_bel())
            graph.add_is_a(gene_node, homologene_node)

    def enrich_equivalences(self, graph):
        """Add equivalent node information.

        :type graph: pybel.BELGraph
        """
        for gene_node, data, entrez_gene in self._iter_gene_data(graph):
            graph.add_equivalence(gene_node, entrez_gene.as_bel())

    def enrich_orthologies(self, graph):
        """Add ortholog relationships to graph.

        :type graph: pybel.BELGraph
        """
        for gene_node, data, entrez_gene in self._iter_gene_data(graph):
            for ortholog in entrez_gene.homologene.genes:
                ortholog_node = ortholog.as_bel()

                if ortholog_node.as_tuple() == gene_node:
                    continue

                graph.add_orthology(gene_node, ortholog_node)

    def count_genes(self) -> int:
        """Count the genes in the database.

        :rtype: int
        """
        return self._count_model(Gene)

    def count_homologenes(self) -> int:
        """Count the HomoloGenes in the database.

        :rtype: int
        """
        return self._count_model(Homologene)

    def count_species(self) -> int:
        """Count the species in the database.

        :rtype: int
        """
        return self._count_model(Species)

    def list_species(self):
        """List all species in the database.

        :rtype: List[Species[
        """
        return self._list_model(Species)

    def list_homologenes(self):
        """List all HomoloGenes in the database.

        :return:
        """
        return self._list_model(Homologene)

    def summarize(self):
        """Return a summary dictionary over the content of the database.

        :rtype: dict[str,int]
        """
        return dict(
            genes=self.count_genes(),
            species=self.count_species(),
            homologenes=self.count_homologenes()
        )

    def list_genes(self, limit=None, offset=None):
        """List genes in the database.

        :param Optional[int] limit:
        :param Optional[int] offset:
        :rtype: List[Gene]
        """
        query = self.session.query(Gene)
        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        return query.all()

    @staticmethod
    def _cli_add_populate(main):
        """Overwrite the populate method since it needs to check tax identifiers.

        :type main: click.Group
        :rtype: click.Group
        """
        return add_populate_to_cli(main)


def add_populate_to_cli(main):
    """Add a custom population function to the command line interface.

    :type main: click.Group
    :rtype: click.Group
    """
    @main.command()
    @click.option('--reset', is_flag=True, help='Nuke database first')
    @click.option('--force', is_flag=True, help='Force overwrite if already populated')
    @click.option('-t', '--tax-id', default=DEFAULT_TAX_IDS, multiple=True,
                  help='Keep this taxonomy identifier. Can specify multiple. Defaults to 9606 (human), 10090 (mouse), 10116'
                       ' (rat), 7227 (fly), and 4932 (yeast).')
    @click.option('-a', '--all-tax-id', is_flag=True, help='Use all taxonomy identifiers')
    @click.pass_obj
    def populate(manager, reset, force, tax_id, all_tax_id):
        """Populate the database."""
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
