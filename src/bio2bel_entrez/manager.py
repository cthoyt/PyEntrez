# -*- coding: utf-8 -*-

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from pybel.constants import FUNCTION, GENE, IDENTIFIER, NAME, NAMESPACE
from .constants import DEFAULT_CACHE_CONNECTION
from .models import Base, Gene, Homologene, Species, Xref
from .parser import get_entrez_df, get_homologene_df

log = logging.getLogger(__name__)


class Manager(object):
    """Manages the Entrez Gene database"""

    def __init__(self, connection=None, echo=False, autoflush=False, expire_on_commit=True):
        """
        :param Optional[str] connection: SQLAlchemy
        :param bool echo: True or False for SQL output of SQLAlchemy engine
        """
        self.connection = connection or DEFAULT_CACHE_CONNECTION
        log.info('using connection %s', self.connection)
        self.engine = create_engine(self.connection, echo=echo)
        self.session_maker = sessionmaker(
            bind=self.engine,
            autoflush=autoflush,
            expire_on_commit=expire_on_commit
        )
        self.session = self.session_maker()
        self.create_all()

        self.species_cache = {}
        self.gene_cache = {}
        self.homologene_cache = {}
        self.gene_homologene = {}

    def create_all(self, check_first=True):
        """Create tables"""
        Base.metadata.create_all(self.engine, checkfirst=check_first)

    def drop_all(self, check_first=True):
        """Create tables"""
        log.info('dropping tables')
        Base.metadata.drop_all(self.engine, checkfirst=check_first)

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

        log.info('committing HomoloGene models')
        self.session.commit()

    def populate_gene_info(self, url=None, cache=True, force_download=False, interval=None, tax_id_filter=None):
        """Populates the database (assumes it's already empty)

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
        for taxonomy_id, sub_df in df.groupby('#tax_id'):
            taxonomy_id = str(int(taxonomy_id))
            species = self.get_or_create_species(taxonomy_id=taxonomy_id)

            for idx, _, entrez_id, name, xrefs, description, type_of_gene in tqdm(sub_df.itertuples(),
                                                                                  desc='Tax ID {}'.format(taxonomy_id),
                                                                                  total=len(sub_df.index)):
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

        if namespace is None or namespace not in {'EGID', 'EG', 'ENTREZ'}:
            return

        if IDENTIFIER in data:
            return self.get_gene_by_entrez_id(entrez_id=data[IDENTIFIER])
        elif NAME in data:
            return self.get_gene_by_entrez_id(entrez_id=data[NAME])
        else:
            raise IndexError

    def _iter_gene_data(self, graph):
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
            homologene_node = graph.add_node_from_data(gene.homologene.to_pybel())
            graph.add_is_a(gene_node, homologene_node)

    def enrich_orthologies(self, graph):
        """Adds ortholog relationships to graph

        :type graph: pybel.BELGraph
        """
        for gene_node, data, gene in self._iter_gene_data(graph):
            for ortholog in gene.homologene.genes:
                ortholog_node = ortholog.to_pybel()

                if ortholog_node.to_tuple() == gene_node:
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

    def list_genes(self, limit=None, offset=None):
        query = self.session.query(Gene)
        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        return query.all()


if __name__ == '__main__':
    logging.basicConfig(level=20, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    log.setLevel(20)
    m = Manager(connection='sqlite:////Users/cthoyt/Desktop/test_entrez.db')
    m.drop_all()
    m.create_all()
    # turl =  '/Users/cthoyt/.pybel/bio2bel/entrez/Saccharomyces_cerevisiae.gene_info.gz'
    turl = None
    tidf = {'9606', '4932', '559292'}
    m.populate(gene_info_url=turl, tax_id_filter=tidf)
