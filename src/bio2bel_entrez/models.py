# -*- coding: utf-8 -*-

"""SQLAlchemy models for Bio2BEL Entrez."""

from typing import Mapping, Optional

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import backref, relationship

from pybel.dsl import CentralDogma, FUNC_TO_DSL, gene
from .constants import ENCODING, MODULE_NAME

GENE_TABLE_NAME = f'{MODULE_NAME}_gene'
GROUP_TABLE_NAME = f'{MODULE_NAME}_homologene'
SPECIES_TABLE_NAME = f'{MODULE_NAME}_species'
XREF_TABLE_NAME = f'{MODULE_NAME}_xref'

Base: DeclarativeMeta = declarative_base()


class Species(Base):
    """Represents a Species."""

    __tablename__ = SPECIES_TABLE_NAME
    id = Column(Integer, primary_key=True)

    taxonomy_id = Column(String(32), unique=True, nullable=False, index=True, doc='NCBI Taxonomy Identifier')

    def __repr__(self):  # noqa: D105
        return f'<Species taxonomy_id={self.taxonomy_id}>'


class Homologene(Base):
    """Represents a HomoloGene Group."""

    __tablename__ = GROUP_TABLE_NAME
    id = Column(Integer, primary_key=True)

    homologene_id = Column(String(255), index=True, unique=True, nullable=False)

    bel_encoding = 'GRP'

    def as_bel(self, func: Optional[str] = None) -> CentralDogma:
        """Make a PyBEL DSL object from this HomoloGene."""
        dsl = gene if func is None else FUNC_TO_DSL[func]

        return dsl(
            namespace='homologene',
            name=str(self.homologene_id),
            identifier=str(self.homologene_id),
        )

    def __repr__(self):  # noqa: D105
        return f'<HomoloGene id={self.homologene_id}>'


class Gene(Base):
    """Represents a gene."""

    __tablename__ = GENE_TABLE_NAME

    id = Column(Integer, primary_key=True)

    species_id = Column(Integer, ForeignKey(f'{Species.__tablename__}.id'), index=True)
    species = relationship('Species', backref=backref('genes'))

    entrez_id = Column(String(32), nullable=False, index=True, doc='NCBI Entrez Gene Identifier')
    name = Column(String(255), doc='Entrez Gene Symbol')
    description = Column(Text, doc='Gene Description')
    type_of_gene = Column(String(32), doc='Type of Gene')

    # modification_date = Column(Date)

    homologene_id = Column(Integer, ForeignKey(f'{Homologene.__tablename__}.id'))
    homologene = relationship(Homologene, backref=backref('genes'))

    @property
    def bel_encoding(self) -> str:
        """Return the BEL encoding."""
        return ENCODING.get(self.type_of_gene, 'GRP')

    def as_bel(self, func=None) -> CentralDogma:
        """Make a PyBEL DSL object from this gene."""
        dsl = gene if func is None else FUNC_TO_DSL[func]

        return dsl(
            namespace=MODULE_NAME,
            name=str(self.name),
            identifier=str(self.entrez_id),
        )

    @property
    def is_transcribed(self) -> bool:
        """Return if this gene can be transcribed to an RNA."""
        raise NotImplementedError

    @property
    def is_translated(self) -> bool:
        """Return if this gene can be translated to a protein."""
        raise NotImplementedError

    def to_json(self) -> Mapping[str, int]:
        """Return this Gene as a JSON dictionary."""
        return dict(
            entrez_id=str(self.entrez_id),
            name=str(self.name),
            species=str(self.species),
            description=str(self.description),
            type=str(self.type_of_gene),
        )

    def __repr__(self):  # noqa: D105
        return f'<Gene entrez_id={self.entrez_id}, name={self.name}>'

    __table_args__ = (
        Index('species-name-index', species_id, name),  # for fast queries on a specific species' names
    )


class Xref(Base):
    """Represents a database cross reference."""

    __tablename__ = XREF_TABLE_NAME

    id = Column(Integer, primary_key=True)

    gene_id = Column(Integer, ForeignKey(f'{Gene.__tablename__}.id'), index=True)
    gene = relationship(Gene, backref=backref('xrefs'))

    database = Column(String(64), doc='Database name', index=True)
    value = Column(String(255), doc='Database entry name')

    __table_args__ = (
        Index('gene-database-value-index', gene_id, database, value),
        # UniqueConstraint(gene_id, database, value),
    )
