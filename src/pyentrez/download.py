# -*- coding: utf-8 -*-

import abc
import configparser
import logging
import os

import pandas as pd
import six
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .models import Base, Species, Gene

try:
    from urllib.request import urlretrieve
except:
    from urllib import urlretrieve

log = logging.getLogger(__name__)

URL = 'ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz'
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'pyentrez')

if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.ini')

DATA_DIR = os.path.join(os.path.expanduser('~'), '.pyentrez')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DATA_PATH = os.path.join(DATA_DIR, 'gene_info.gz')

DATABASE_PATH = 'sqlite:///' + os.path.join(DATA_DIR, 'pyentrez.db')


def download(force_download=False):
    """Downloads the Entrez Gene Info

    :param bool force_download:
    """
    if force_download or not os.path.exists(DATA_PATH):
        log.info('Downloading {}'.format(DATA_PATH))
        urlretrieve(URL, DATA_PATH)


def load(force_download=False):
    """Loads the Entrez Gene info in a data frame

    :rtype: pandas.DataFrame
    """
    download(force_download=force_download)

    log.info('Loading data from local path %s', DATA_PATH)
    return pd.read_csv(DATA_PATH, sep='\t', na_values=['-', 'NEWENTRY'])


@six.add_metaclass(abc.ABCMeta)
class AbstractManager(object):
    """Abstract class representing a Manager"""

    def __init__(self, connection=None, echo=False, autoflush=False, expire_on_commit=True):
        """
        :param str connection: SQLAlchemy
        :param bool echo: True or False for SQL output of SQLAlchemy engine
        """
        self.connection = self.get_connection_string(connection)
        self.engine = create_engine(self.connection, echo=echo)
        self.session_maker = sessionmaker(
            bind=self.engine,
            autoflush=autoflush,
            expire_on_commit=expire_on_commit
        )
        self.session = scoped_session(self.session_maker)
        self.create_tables()

    @abc.abstractmethod
    def create_tables(self):
        """Creates tables"""


def make_manager(base, config_file_path, default_db):
    """

    :param base:
    :param config_file_path:
    :param default_db:
    :rtype: AbstractManager
    """

    class ConcreteManager(AbstractManager):
        """Creates a connection to database and a persistent session using SQLAlchemy"""

        def create_tables(self, check_first=True):
            """Creates all tables from models in your database

            :param bool check_first: Check if tables already exists
            """
            log.info('create tables in {}'.format(self.engine.url))
            base.metadata.create_all(self.engine, checkfirst=check_first)

        def drop_tables(self):
            """Drops all tables in the database"""
            log.info('drop tables in {}'.format(self.engine.url))
            base.metadata.drop_all(self.engine)

        @staticmethod
        def get_connection_string(connection=None):
            """Return SQLAlchemy connection string if it is set

            :param str connection: get the SQLAlchemy connection string
            :rtype: str
            """
            if connection:
                return connection

            config = configparser.ConfigParser()

            if os.path.exists(config_file_path):
                log.info('fetch database configuration from {}'.format(config_file_path))
                config.read(config_file_path)
                connection = config['database']['sqlalchemy_connection_string']
                log.info('load connection string from {}: {}'.format(config_file_path, connection))
                return connection

            with open(config_file_path, 'w') as config_file:
                config['database'] = {'sqlalchemy_connection_string': default_db}
                config.write(config_file)
                log.info('create configuration file {}'.format(config_file_path))

            return default_db

    return ConcreteManager


Manager = make_manager(Base, CONFIG_PATH, DATABASE_PATH)

columns = [
    '#tax_id',
    'GeneID',
    'Symbol',
    'description',
    'type_of_gene',
]


class PopulateManager(Manager):
    """Manages insertions in the database"""

    def populate(self, interval=1000):
        """Populates the database"""
        df = load()

        log.info('Beginning to populate database')

        tax_map = {}

        counter = 0

        for _, tax_id, gene_id, symbol, description, type_of_gene in df[columns].itertuples():
            counter += 1

            tax_id = int(tax_id)
            gene_id = int(gene_id)

            tax_model = tax_map.get(tax_id)

            if tax_model is None:
                tax_model = Species(tax_id=tax_id)
                tax_map[tax_id] = tax_model

            gene = Gene(
                tax=tax_model,
                gene_id=gene_id,
                symbol=symbol,
                description=description,
                type_of_gene=type_of_gene,
            )

            self.session.add(gene)

            if counter % interval == 0:
                counter = 0
                self.session.commit()

        self.session.commit()
