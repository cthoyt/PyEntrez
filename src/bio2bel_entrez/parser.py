# -*- coding: utf-8 -*-

"""Parsers for Entrez and HomoloGene data."""

from bio2bel.downloading import make_df_getter
from .constants import (
    GENE_INFO_COLUMNS, GENE_INFO_DATA_PATH, GENE_INFO_URL, HOMOLOGENE_COLUMNS, HOMOLOGENE_DATA_PATH, HOMOLOGENE_URL,
)

__all__ = [
    'get_gene_info_df',
    'get_homologene_df',
]

get_gene_info_df = make_df_getter(
    GENE_INFO_URL,
    GENE_INFO_DATA_PATH,
    sep='\t',
    na_values=['-', 'NEWENTRY'],
    usecols=GENE_INFO_COLUMNS,
)

get_homologene_df = make_df_getter(
    HOMOLOGENE_URL,
    HOMOLOGENE_DATA_PATH,
    sep='\t',
    names=HOMOLOGENE_COLUMNS,
)
"""Download the HomoloGene data.

Columns:

    1) HID (HomoloGene group id)
    2) Taxonomy ID
    3) Gene ID
    4) Gene Symbol
    5) Protein gi
    6) Protein accession"""
