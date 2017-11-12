# -*- coding: utf-8 -*-

import logging
import os

import pandas as pd

from pyentrez.constants import DATA_PATH, GENE_INFO_URL, columns

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

log = logging.getLogger(__name__)


def download_data(force_download=False):
    """Downloads the Entrez Gene Info

    :param bool force_download: If true, overwrites a previously cached file
    """
    if os.path.exists(DATA_PATH) and not force_download:
        log.info('using cached data at %s', DATA_PATH)
    else:
        log.info('downloading %s to %s', GENE_INFO_URL, DATA_PATH)
        urlretrieve(GENE_INFO_URL, DATA_PATH)

    return DATA_PATH


def get_entrez_df(url=None, cache=True, force_download=False):
    """Loads the Entrez Gene info in a data frame

    :param Optional[str] url: A custom path to use for data
    :param bool cache: If true, the data is downloaded to the file system, else it is loaded from the internet
    :param bool force_download: If true, overwrites a previously cached file
    :rtype: pandas.DataFrame
    """
    if url is None and cache:
        url = download_data(force_download=force_download)

    df = pd.read_csv(
        url or GENE_INFO_URL,
        sep='\t',
        na_values=['-', 'NEWENTRY'],
        usecols=columns
    )

    return df
