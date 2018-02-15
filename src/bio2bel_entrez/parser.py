# -*- coding: utf-8 -*-

import logging
import os
from urllib.request import urlretrieve

import pandas as pd

from .constants import (
    GENE_INFO_DATA_PATH, GENE_INFO_URL, HOMOLOGENE_DATA_PATH, HOMOLOGENE_URL, gene_info_columns, homologene_columns,
)

log = logging.getLogger(__name__)


def download_gene_info(force_download=False):
    """Downloads the Entrez Gene Info

    :param bool force_download: If true, overwrites a previously cached file
    :rtype: str
    """
    if os.path.exists(GENE_INFO_DATA_PATH) and not force_download:
        log.info('using cached data at %s', GENE_INFO_DATA_PATH)
    else:
        log.info('downloading %s to %s', GENE_INFO_URL, GENE_INFO_DATA_PATH)
        urlretrieve(GENE_INFO_URL, GENE_INFO_DATA_PATH)

    return GENE_INFO_DATA_PATH


def download_homologene(force_download=False):
    """Downloads Homologene

    :param bool force_download: If true, overwrites a previously cached file
    :rtype: str
    """
    if os.path.exists(HOMOLOGENE_DATA_PATH) and not force_download:
        log.info('using cached data at %s', HOMOLOGENE_DATA_PATH)
    else:
        log.info('downloading %s to %s', HOMOLOGENE_URL, HOMOLOGENE_DATA_PATH)
        urlretrieve(HOMOLOGENE_URL, HOMOLOGENE_DATA_PATH)

    return HOMOLOGENE_DATA_PATH


def get_entrez_df(url=None, cache=True, force_download=False):
    """Loads the Entrez Gene info in a data frame

    :param Optional[str] url: A custom path to use for data
    :param bool cache: If true, the data is downloaded to the file system, else it is loaded from the internet
    :param bool force_download: If true, overwrites a previously cached file
    :rtype: pandas.DataFrame
    """
    if url is None and cache:
        url = download_gene_info(force_download=force_download)

    df = pd.read_csv(
        url or GENE_INFO_URL,
        sep='\t',
        na_values=['-', 'NEWENTRY'],
        usecols=gene_info_columns
    )

    return df


def get_homologene_df(url=None, cache=True, force_download=False):
    """Downloads the Homologene cache

    Columns:

    1) HID (HomoloGene group id)
    2) Taxonomy ID
    3) Gene ID
    4) Gene Symbol
    5) Protein gi
    6) Protein accession

    :param Optional[str] url: A custom URL to download
    :param bool cache: If true, the data is downloaded to the file system, else it is loaded from the internet
    :param bool force_download: If true, overwrites a previously cached file
    :rtype: pandas.DataFrame
    """
    if url is None and cache:
        url = download_homologene(force_download=force_download)

    df = pd.read_csv(
        url or HOMOLOGENE_URL,
        sep='\t',
        names=homologene_columns
    )

    return df
