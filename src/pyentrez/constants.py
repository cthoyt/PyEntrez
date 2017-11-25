# -*- coding: utf-8 -*-

import os

from bio2bel.utils import get_connection, get_data_dir

MODULE_NAME = 'entrez'

DATA_DIR = get_data_dir(MODULE_NAME)
DEFAULT_CACHE_CONNECTION = get_connection(MODULE_NAME)

GENE_INFO_URL = 'ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz'
DATA_PATH = os.path.join(DATA_DIR, 'gene_info.gz')

#: Columns fro gene_info.gz that are used
columns = [
    '#tax_id',
    'GeneID',
    'Symbol',
    'dbXrefs',
    'description',
    'type_of_gene',
]
