# -*- coding: utf-8 -*-

"""Manager for Bio2BEL Entrez."""

import logging
import time

from sqlalchemy import and_
from tqdm import tqdm

from bio2bel.namespace_manager import NamespaceManagerMixin
from pybel.constants import FUNCTION, GENE, IDENTIFIER, NAME, NAMESPACE
from pybel.manager.models import NamespaceEntry
from .cli_utils import add_populate_to_cli
from .constants import MODULE_NAME
from .models import Base, Gene, Homologene, Species, Xref
from .parser import get_entrez_df, get_homologene_df

__all__ = [
    'species_consortium_mapping',
    'consortium_species_mapping',
    'Manager',
]

log = logging.getLogger(__name__)

species_consortium_mapping = {
    10090: 'MGI',
    10116: 'RGD',
    4932: 'SGD',
    7227: 'FLYBASE',
    9606: 'HGNC'
}

consortium_species_mapping = {v: k for k, v in species_consortium_mapping.items()}


class Manager(NamespaceManagerMixin):
    """Manages the Entrez Gene database"""

    module_name = MODULE_NAME
    flask_admin_models = [Gene, Homologene, Species, Xref]
    namespace_model = Gene

    def __init__(self, *args, **kwargs):
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
    def _get_identifier(model):
        return model.entrez_id

    def _create_namespace_entry_from_model(self, model, namespace):
        return NamespaceEntry(
            encoding='G',
            name=model.name,
            identifier=model.entrez_id,
            namespace=namespace,
        )

    def get_or_create_species(self, taxonomy_id, **kwargs):
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
        """Looks up a gene by entrez identifier

        :param str entrez_id: Entrez gene identifier
        :rtype: Optional[Gene]
        """
        return self.session.query(Gene).filter(Gene.entrez_id == entrez_id).one_or_none()

    def get_gene_by_rgd_name(self, name):
        rgd_name_filter = and_(Species.taxonomy_id == '10116', Gene.name == name)
        return self.session.query(Gene).join(Species).filter(rgd_name_filter).one_or_none()

    def get_gene_by_mgi_name(self, name):
        mgi_name_filter = and_(Species.taxonomy_id == '10090', Gene.name == name)
        return self.session.query(Gene).join(Species).filter(mgi_name_filter).one_or_none()

    def get_gene_by_hgnc_name(self, name):
        hgnc_name_filter = and_(Species.taxonomy_id == '9606', Gene.name == name)
        return self.session.query(Gene).join(Species).filter(hgnc_name_filter).one_or_none()

    def get_or_create_gene(self, entrez_id, **kwargs):
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
        """Populates the database

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
        """Populates the database (assumes it's already empty)

        :param Optional[str] url: A custom url to download
        :param Optional[int] interval: The number of records to commit at a time
        :param bool cache: If true, the data is downloaded to the file system, else it is loaded from the internet
        :param bool force_download: If true, overwrites a previously cached file
        :param Optional[set[str]] tax_id_filter: Species to keep
        """
        t = time.time()
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
        """Populates the database (assumes it's already empty)

        :param Optional[str] gene_info_url: A custom url to download
        :param Optional[int] interval: The number of records to commit at a time
        :param Optional[set[str]] tax_id_filter: Species to keep
        :param Optional[str] homologene_url: A custom url to download
        """
        self.populate_homologene(url=homologene_url, tax_id_filter=tax_id_filter)
        self.populate_gene_info(url=gene_info_url, interval=interval, tax_id_filter=tax_id_filter)

    def lookup_node(self, data):
        """Looks up a gene from a PyBEL data dictionary

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

        if namespace in {'EGID', 'EG', 'ENTREZ'}:
            if identifier:
                return self.get_gene_by_entrez_id(identifier)
            elif name:
                return self.get_gene_by_entrez_id(name)
            else:
                raise IndexError

        if namespace == 'MGI':
            if name:
                return self.get_gene_by_mgi_name(name)

        if namespace == 'RGD':
            if name:
                return self.get_gene_by_rgd_name(name)

    def _iter_gene_data(self, graph):
        """

        :param pybel.BELGraph graph:
        :rtype: tuple[tuple,dict,Gene]
        """
        for gene_node, data in graph.nodes(data=True):
            gene = self.lookup_node(data)

            if gene is None:
                continue

            yield gene_node, data, gene

    def enrich_genes_with_homologenes(self, graph):
        """Adds HomoloGene parents to graph

        :type graph: pybel.BELGraph
        """
        for gene_node, data, gene in self._iter_gene_data(graph):
            homologene_node = graph.add_node_from_data(gene.homologene.as_bel())
            graph.add_is_a(gene_node, homologene_node)

    def enrich_orthologies(self, graph):
        """Adds ortholog relationships to graph

        :type graph: pybel.BELGraph
        """
        for gene_node, data, gene in self._iter_gene_data(graph):
            for ortholog in gene.homologene.genes:
                ortholog_node = ortholog.as_bel()

                if ortholog_node.as_tuple() == gene_node:
                    continue

                graph.add_orthology(gene_node, ortholog_node)

    def count_genes(self):
        """Counts the genes in the database

        :rtype: int
        """
        return self.session.query(Gene).count()

    def count_homologenes(self):
        """Counts the HomoloGenes in the database

        :rtype: int
        """
        return self.session.query(Homologene).count()

    def count_species(self):
        """Counts the species in the database

        :rtype: int
        """
        return self.session.query(Species).count()

    def list_species(self):
        return self.session.query(Species).all()

    def summarize(self):
        """Returns a summary dictionary over the content of the database

        :rtype: dict[str,int]
        """
        return dict(
            genes=self.count_genes(),
            species=self.count_species(),
            homologenes=self.count_homologenes()
        )

    def list_genes(self, limit=None, offset=None):
        query = self.session.query(Gene)
        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        return query.all()

    @staticmethod
    def _cli_add_populate(main):
        """Overwrite the populate method since it needs to check tax identifiers"""
        return add_populate_to_cli(main)
