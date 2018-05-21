# -*- coding: utf-8 -*-

from pybel.dsl import gene
from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

from .constants import MODULE_NAME

GENE_TABLE_NAME = '{}_gene'.format(MODULE_NAME)
GROUP_TABLE_NAME = '{}_homologene'.format(MODULE_NAME)
SPECIES_TABLE_NAME = '{}_species'.format(MODULE_NAME)
XREF_TABLE_NAME = '{}_xref'.format(MODULE_NAME)

Base = declarative_base()


class Species(Base):
    """Represents a Species"""
    __tablename__ = SPECIES_TABLE_NAME

    id = Column(Integer, primary_key=True)

    taxonomy_id = Column(String(32), unique=True, nullable=False, index=True, doc='NCBI Taxonomy Identifier')

    def __repr__(self):
        return str(self.taxonomy_id)


class Gene(Base):
    """Represents a Gene."""

    __tablename__ = GENE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    species_id = Column(Integer, ForeignKey('{}.id'.format(SPECIES_TABLE_NAME)), index=True)
    species = relationship('Species', backref=backref('genes'))

    entrez_id = Column(String(32), nullable=False, index=True, doc='NCBI Entrez Gene Identifier')
    name = Column(String(255), doc='Entrez Gene Symbol')
    description = Column(Text, doc='Gene Description')
    type_of_gene = Column(String(32), doc='Type of Gene')

    # modification_date = Column(Date)

    homologene_id = Column(Integer, ForeignKey('{}.id'.format(GROUP_TABLE_NAME)))
    homologene = relationship('Homologene', backref=backref('genes'))

    def __repr__(self):
        return self.entrez_id

    def as_bel(self):
        """Make PyBEL node data dictionary.

        :rtype: dict
        """
        return gene(
            namespace='ENTREZ',
            name=str(self.name),
            identifier=str(self.entrez_id)
        )

    def to_json(self):
        """Returns this as a JSON dictionary.

        :rtype: dict
        """
        return dict(
            entrez_id=str(self.entrez_id),
            name=str(self.name),
            species=str(self.species),
            description=str(self.description),
            type=str(self.type_of_gene),
        )


class Xref(Base):
    """Represents a database cross reference."""

    __tablename__ = XREF_TABLE_NAME

    id = Column(Integer, primary_key=True)

    gene_id = Column(Integer, ForeignKey('{}.id'.format(GENE_TABLE_NAME)), index=True)
    gene = relationship('Gene', backref=backref('xrefs'))

    database = Column(String(64), doc='Database name', index=True)
    value = Column(String(255), doc='Database entry name')

    __table_args__ = (
        Index(gene_id, database, value),
        # UniqueConstraint(gene_id, database, value),
    )


class Homologene(Base):
    """Represents a HomoloGene Group."""

    __tablename__ = GROUP_TABLE_NAME

    id = Column(Integer, primary_key=True)

    homologene_id = Column(String(255), index=True, unique=True, nullable=False)

    def __str__(self):
        return self.homologene_id

    def to_bel(self):
        """Make PyBEL node data dictionary

        :rtype: dict
        """
        return gene(
            namespace='HOMOLOGENE',
            name=str(self.homologene_id),
            identifier=str(self.homologene_id)
        )
