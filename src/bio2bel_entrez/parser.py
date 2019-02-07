# -*- coding: utf-8 -*-

"""Parsers for Entrez and HomoloGene data."""
import logging
from typing import Iterable, Mapping, Optional, Tuple

import pandas as pd

from bio2bel.downloading import make_df_getter
from .constants import (
    GENE_INFO_COLUMNS, GENE_INFO_DATA_PATH, GENE_INFO_URL, GENE_REFSEQ_PATH, GENE_REFSEQ_URL,
    HOMOLOGENE_COLUMNS, HOMOLOGENE_DATA_PATH, HOMOLOGENE_URL,
)

__all__ = [
    'get_gene_info_df',
    'get_homologene_df',
    'get_refseq_df',
    'postprocess_refseq_df',
    'get_gene_positions',
]

logger = logging.getLogger(__name__)

get_gene_info_df = make_df_getter(
    GENE_INFO_URL,
    GENE_INFO_DATA_PATH,
    sep='\t',
    index_col='GeneID',
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

get_refseq_df = make_df_getter(
    GENE_REFSEQ_URL,
    GENE_REFSEQ_PATH,
    sep='\t',
    index_col='GeneID',
    # names=GENE_REFSEQ_COLUMNS,
    na_values=['-', 'NEWENTRY'],
    usecols=['#tax_id', 'GeneID', 'status', 'start_position_on_the_genomic_accession',
             'end_position_on_the_genomic_accession', 'assembly'],
)


def postprocess_refseq_df(refseq_df: pd.DataFrame) -> pd.DataFrame:
    """Postprocess the RefSeq data frame."""
    # make sure its not suppressed
    refseq_df = refseq_df[refseq_df['status'] != 'SUPPRESSED']
    # make sure there's an assembly
    refseq_df = refseq_df[refseq_df['assembly'].notna()]
    # only take the stuff we care about,
    # and drop all the duplicates (there are many, and everything after is unique!)
    refseq_df = refseq_df[[
        'start_position_on_the_genomic_accession',
        'end_position_on_the_genomic_accession',
    ]].drop_duplicates()

    refseq_df.start_position_on_the_genomic_accession = refseq_df.start_position_on_the_genomic_accession.map(int)
    refseq_df.end_position_on_the_genomic_accession = refseq_df.end_position_on_the_genomic_accession.map(int)
    return refseq_df


def get_gene_positions(tax_ids: Optional[Iterable[str]] = None, **kwargs) -> Mapping[str, Tuple[int, int]]:
    """Get a mapping from Entrez Gene identifiers to the start/end positions."""
    df: pd.DataFrame = get_refseq_df(**kwargs)
    if tax_ids is not None:
        tax_ids = {int(tax_id) for tax_id in tax_ids}
        logger.info(f'filtering RefSeq to {", ".join(map(str, tax_ids))}')
        df = df[df['#tax_id'].isin(tax_ids)]
    df = postprocess_refseq_df(df)

    return {
        str(gene_id): (start, end)
        for gene_id, (start, end) in df.iterrows()
    }
