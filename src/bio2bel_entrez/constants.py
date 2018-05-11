# -*- coding: utf-8 -*-

import os

from bio2bel import get_data_dir

MODULE_NAME = 'entrez'
DATA_DIR = get_data_dir(MODULE_NAME)

GENE_INFO_URL = 'ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz'
GENE_INFO_DATA_PATH = os.path.join(DATA_DIR, 'gene_info.gz')
HOMOLOGENE_DATA_PATH = os.path.join(DATA_DIR, 'homologene.data')

#: Columns fro gene_info.gz that are used
gene_info_columns = [
    '#tax_id',
    'GeneID',
    'Symbol',
    'dbXrefs',
    'description',
    'type_of_gene',
]

HOMOLOGENE_BUILD_URL = 'ftp://ftp.ncbi.nih.gov/pub/HomoloGene/current/RELEASE_NUMBER'
HOMOLOGENE_URL = 'ftp://ftp.ncbi.nih.gov/pub/HomoloGene/current/homologene.data'

homologene_columns = [
    'homologene_id',
    'tax_id',
    'gene_id',
    'gene_symbol',
    'protein_gi',
    'protein_accession'
]

default_tax_ids = [
    '9606',  # Human
    '10090',  # Mouse
    '10116',  # Rat
    '7227',  # Drosophila
    '4932',  # Yeast
]
