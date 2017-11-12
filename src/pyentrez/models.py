# -*- coding: utf-8 -*-

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

TABLE_PREFIX = 'entrez'
GENE_TABLE_NAME = '{}_gene'.format(TABLE_PREFIX)
SPECIES_TABLE_NAME = '{}_species'.format(TABLE_PREFIX)
XREF_TABLE_NAME = '{}_xref'.format(TABLE_PREFIX)

Base = declarative_base()


class Species(Base):
    """Represents a Species"""
    __tablename__ = SPECIES_TABLE_NAME

    id = Column(Integer, primary_key=True)

    taxonomy_id = Column(Integer, unique=True, nullable=False, index=True, doc='NCBI Taxonomy Identifier')

    def __repr__(self):
        return str(self.taxonomy_id)


class Gene(Base):
    """Represents a Gene"""
    __tablename__ = GENE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    species_id = Column(Integer, ForeignKey('{}.id'.format(SPECIES_TABLE_NAME)), index=True)
    species = relationship('Species', backref=backref('genes'))

    entrez_id = Column(Integer, nullable=False, index=True, doc='NCBI Entrez Gene Identifier')
    entrez_symbol = Column(String, doc='Entrez Gene Symbol')
    description = Column(String, doc='Gene Description')
    type_of_gene = Column(String, doc='Type of Gene')

    # modification_date = Column(Date)

    def __repr__(self):
        return '<Entrez {}>'.format(self.entrez_id)


class Xref(Base):
    """Represents a database cross reference"""
    __tablename__ = XREF_TABLE_NAME

    id = Column(Integer, primary_key=True)

    gene_id = Column(Integer, ForeignKey('{}.id'.format(GENE_TABLE_NAME)), index=True)
    gene = relationship('Gene', backref=backref('xrefs'))

    database = Column(String, doc='Database name', index=True)
    value = Column(String, doc='Database entry name')
