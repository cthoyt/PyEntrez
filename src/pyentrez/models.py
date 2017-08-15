# -*- coding: utf-8 -*-

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

Base = declarative_base()


class Species(Base):
    """Species"""
    __tablename__ = 'pyentrez_species'

    id = Column(Integer, primary_key=True)

    tax_id = Column(Integer, unique=True, doc='Taxonomy Identifier')

    def __repr__(self):
        return '<Species {}>'.format(self.tax_id)


class Gene(Base):
    """Entrez Gene"""
    __tablename__ = 'pyentrez_gene'

    id = Column(Integer, primary_key=True)

    tax_id = Column(Integer, ForeignKey('pyentrez_species.id'), index=True)
    tax = relationship('Species', backref=backref('genes'))

    gene_id = Column(Integer, unique=True, nullable=False, doc='Entrez Gene Identifier')
    symbol = Column(String, doc='Entrez Gene Symbol')
    description = Column(String, doc='Gene Description')
    type_of_gene = Column(String, doc='Type of Gene')

    # modification_date = Column(Date)

    def __repr__(self):
        return '<Entrez {}>'.format(self.gene_id)
