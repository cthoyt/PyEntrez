# -*- coding: utf-8 -*-

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from pyentrez.constants import DEFAULT_CACHE_CONNECTION
from pyentrez.models import Base, Gene, Species, Xref
from pyentrez.parser import get_entrez_df

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

    def get_or_create_gene(self, gene_id, **kwargs):
        gene = self.session.query(Gene).filter(Gene.gene_id == gene_id).one_or_none()

        if gene is None:
            gene = Gene(gene_id=gene_id, **kwargs)

        return gene

    def populate(self, url=None, interval=500000, tax_id_filter=None):  # TODO multi-threading?
        """Populates the database (assumes it's already empty)

        :param Optional[str] url: A custom url to download
        :param Optional[int] interval: The number of records to commit at a time
        :param Optional[set[int]] tax_id_filter: Species to keep
        """
        log.info('downloading data')
        df = get_entrez_df(url=url)

        if tax_id_filter is not None:
            log.info('filtering to %s', tax_id_filter)
            df = df[df['#tax_id'].isin(tax_id_filter)]

        log.info('preparing models')
        species_cache = {}

        for idx, tax_id, gene_id, symbol, xrefs, description, type_of_gene in tqdm(df.itertuples(),
                                                                                   total=len(df.index)):
            tax_id = int(tax_id)
            gene_id = int(gene_id)

            species = species_cache.get(tax_id)

            if species is None:
                species = Species(taxonomy_id=tax_id)
                species_cache[tax_id] = species
                self.session.add(species)

            gene = Gene(
                species=species,
                entrez_id=gene_id,
                entrez_symbol=symbol,
                description=description,
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

    def populate_multithread(self):
        raise NotImplementedError


if __name__ == '__main__':
    logging.basicConfig(level=20, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    log.setLevel(20)
    m = Manager()
    m.drop_all()
    m.create_all()
    # turl =  '/Users/cthoyt/.pybel/bio2bel/entrez/Saccharomyces_cerevisiae.gene_info.gz'
    turl = None
    tidf = {9606, 4932, 559292}
    m.populate(url=turl, tax_id_filter=tidf)
