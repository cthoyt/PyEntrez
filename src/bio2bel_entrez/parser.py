# -*- coding: utf-8 -*-

"""Parsers for Entrez and HomoloGene data."""

import os

import pandas as pd

from bio2bel.downloading import make_df_getter
from .constants import (
    GENE2REFSEQ_COLUMNS, GENE2REFSEQ_DATA_PATH, GENE2REFSEQ_HUMAN_DATA_PATH, GENE2REFSEQ_HUMAN_SLIM_DATA_PATH,
    GENE2REFSEQ_URL, GENE_INFO_COLUMNS, GENE_INFO_DATA_PATH, GENE_INFO_URL, HOMOLOGENE_COLUMNS, HOMOLOGENE_DATA_PATH,
    HOMOLOGENE_URL,
)

__all__ = [
    'get_gene_info_df',
    'get_homologene_df',
    'get_refseq_df',
    'get_human_refseq_slim_df',
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

refseq_dtype = {
    '#tax_id': str,
    'GeneID': str,
}

get_refseq_df = make_df_getter(
    GENE2REFSEQ_URL,
    GENE2REFSEQ_DATA_PATH,
    sep='\t',
    usecols=GENE2REFSEQ_COLUMNS,
    dtype=refseq_dtype,
)


def get_human_refseq_df() -> pd.DataFrame:
    """Get the human subset of gene2refseq.gz."""
    if os.path.exists(GENE2REFSEQ_HUMAN_DATA_PATH):
        return pd.read_csv(
            GENE2REFSEQ_HUMAN_DATA_PATH,
            sep='\t',
            dtype=refseq_dtype,
        )

    df = get_refseq_df()
    df = df[df['#tax_id'] == '9606']
    del df['#tax_id']
    df.to_csv(
        GENE2REFSEQ_HUMAN_DATA_PATH,
        sep='\t',
        index=False,
    )
    return df


def get_human_refseq_slim_df() -> pd.DataFrame:
    """Get the human RefSeq coordinates."""
    if os.path.exists(GENE2REFSEQ_HUMAN_SLIM_DATA_PATH):
        return pd.read_csv(
            GENE2REFSEQ_HUMAN_SLIM_DATA_PATH,
            sep='\t',
            dtype=refseq_dtype,
        )

    df = get_human_refseq_df()

    # FIXME still have problem where there are about 49 duplicated genes
    df = df[df['assembly'] == 'Reference GRCh38.p12 Primary Assembly']
    del df['assembly']
    df.drop_duplicates(inplace=True)
    df[[
        'GeneID',
        'Symbol',
        'start_position_on_the_genomic_accession',
        'end_position_on_the_genomic_accession',

    ]].to_csv(
        GENE2REFSEQ_HUMAN_SLIM_DATA_PATH,
        sep='\t',
        index=False,
    )
    return df
