# -*- coding: utf-8 -*-

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from pybel.constants import FUNCTION, GENE, IDENTIFIER, IS_A, NAME, NAMESPACE
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

    def create_all(self, check_first=True):
        """Create tables"""
        Base.metadata.create_all(self.engine, checkfirst=check_first)

    def drop_all(self, check_first=True):
        """Create tables"""
        log.info('dropping tables')
        Base.metadata.drop_all(self.engine, checkfirst=check_first)

    def get_or_create_species(self, taxonomy_id, **kwargs):
        species = self.session.query(Species).filter(Species.taxonomy_id == taxonomy_id).one_or_none()

        if species is None:
            species = Species(taxonomy_id=taxonomy_id, **kwargs)

        return species

    def get_or_create_gene(self, entrez_id, **kwargs):
        gene = self.session.query(Gene).filter(Gene.entrez_id == entrez_id).one_or_none()

        if gene is None:
            gene = Gene(entrez_id=entrez_id, **kwargs)

        return gene

    def populate_gene_info(self, url=None, cache=True, force_download=False, interval=None, tax_id_filter=None):
        """Populates the database (assumes it's already empty)

        :param Optional[str] url: A custom url to download
        :param Optional[int] interval: The number of records to commit at a time
        :param bool cache: If true, the data is downloaded to the file system, else it is loaded from the internet
        :param bool force_download: If true, overwrites a previously cached file
        :param Optional[set[str]] tax_id_filter: Species to keep
        """
        log.info('downloading data')
        df = get_entrez_df(url=url, cache=cache, force_download=force_download)

        if tax_id_filter is not None:
            tax_id_filter = set(tax_id_filter)
            log.info('filtering to %s', tax_id_filter)
            df = df[df['#tax_id'].isin(tax_id_filter)]

        log.info('preparing models')
        species_cache = {}

        for idx, taxonomy_id, entrez_id, name, xrefs, descr, type_of_gene in tqdm(df.itertuples(), desc='Gene Info',
                                                                                  total=len(df.index)):
            taxonomy_id = str(int(taxonomy_id))
            entrez_id = str(int(entrez_id))

            species = species_cache.get(taxonomy_id)

            if species is None:
                species = Species(taxonomy_id=taxonomy_id)
                species_cache[taxonomy_id] = species
                self.session.add(species)

            gene = Gene(
                species=species,
                entrez_id=entrez_id,
                name=name,
                description=descr,
                type_of_gene=type_of_gene,
            )

            if not isinstance(xrefs, float):
                for xref in xrefs.split('|'):
                    database, value = xref.split(':', 1)
                    gene.xrefs.append(Xref(database=database, value=value))

            self.session.add(gene)

            if interval and idx % interval == 0:
                self.session.commit()

        log.info('committing models')
        self.session.commit()

    def populate_homologene(self, url=None, cache=True, force_download=False, tax_id_filter=None):
        """Populates the database

        :param Optional[str] url: Homologene data url
        :param bool cache: If true, the data is downloaded to the file system, else it is loaded from the internet
        :param bool force_download: If true, overwrites a previously cached file
        :param Optional[set[str]] tax_id_filter: Species to keep
        """
        log.info('downloading data')
        df = get_homologene_df(url=url, cache=cache, force_download=force_download)

        if tax_id_filter is not None:
            tax_id_filter = set(tax_id_filter)
            log.info('filtering to %s', tax_id_filter)
            df = df[df['tax_id'].isin(tax_id_filter)]

        #: a cache from group id to its model
        homologene_cache = {}
        #: a cache from (tax id, gene id) to its model
        genes = {}
        #: a cache from NCBI tax id to its model
        species_cache = {}

        log.info('preparing models')
        for _, (homologene_id, taxonomy_id, entrez_id, name, _, _) in tqdm(df.iterrows(), desc='HomoloGene',
                                                                           total=len(df.index)):
            species = species_cache.get(taxonomy_id)
            if species is None:
                species = species_cache[taxonomy_id] = self.get_or_create_species(taxonomy_id=taxonomy_id)
                self.session.add(species)

            gene = genes.get(entrez_id)
            if gene is None:
                gene = genes[entrez_id] = self.get_or_create_gene(entrez_id=entrez_id, name=name, species=species)
                self.session.add(gene)

            group = homologene_cache.get(homologene_id)
            if group is None:
                group = homologene_cache[homologene_id] = Homologene(homologene_id=homologene_id)
                self.session.add(group)

            group.genes.append(gene)

        log.info('committing models')
        self.session.commit()

    def populate(self, gene_info_url=None, interval=None, tax_id_filter=None, homologene_url=None):
        """Populates the database (assumes it's already empty)

        :param Optional[str] gene_info_url: A custom url to download
        :param Optional[int] interval: The number of records to commit at a time
        :param Optional[set[str]] tax_id_filter: Species to keep
        :param Optional[str] homologene_url: A custom url to download
        """
        self.populate_gene_info(url=gene_info_url, interval=interval, tax_id_filter=tax_id_filter)
        self.populate_homologene(url=homologene_url, tax_id_filter=tax_id_filter)

    def get_gene_by_entrez_id(self, entrez_id):
        """Looks up a gene by entrez identifier

        :param str entrez_id: Entrez gene identifier
        :rtype: Optional[Gene]
        """
        return self.session.query(Gene).filter(Gene.entrez_id == entrez_id).one_or_none()

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
