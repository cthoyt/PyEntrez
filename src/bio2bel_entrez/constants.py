# -*- coding: utf-8 -*-

"""Constants for Bio2BEL Entrez."""

import os

from bio2bel import get_data_dir

MODULE_NAME = 'ncbigene'
DATA_DIR = get_data_dir(MODULE_NAME)

GENE_INFO_URL = 'ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz'
GENE_INFO_DATA_PATH = os.path.join(DATA_DIR, 'gene_info.gz')
#: Columns fro gene_info.gz that are used
GENE_INFO_COLUMNS = [
    '#tax_id',
    'GeneID',
    'Symbol',
    'dbXrefs',
    'description',
    'type_of_gene',
]

GENE_REFSEQ_URL = 'ftp://ftp.ncbi.nih.gov/gene/DATA/gene2refseq.gz'
GENE_REFSEQ_PATH = os.path.join(DATA_DIR, 'gene2refseq.gz')
GENE_REFSEQ_COLUMNS = [
    '#tax_id',
    'GeneID',
    'status',
    'RNA_nucleotide_accession.version',
    'RNA_nucleotide_gi',
    'protein_accession.version',
    'protein_gi',
    'genomic_nucleotide_accession.version',
    'genomic_nucleotide_gi',
    'start_position_on_the_genomic_accession',
    'end_position_on_the_genomic_accession',
    'orientation',
    'assembly',
    'mature_peptide_accession.version',
    'mature_peptide_gi',
    'Symbol',
]

HOMOLOGENE_BUILD_URL = 'ftp://ftp.ncbi.nih.gov/pub/HomoloGene/current/RELEASE_NUMBER'
HOMOLOGENE_URL = 'ftp://ftp.ncbi.nih.gov/pub/HomoloGene/current/homologene.data'
HOMOLOGENE_DATA_PATH = os.path.join(DATA_DIR, 'homologene.data')

HOMOLOGENE_COLUMNS = [
    'homologene_id',
    'tax_id',
    'gene_id',
    'gene_symbol',
    'protein_gi',
    'protein_accession'
]

DEFAULT_TAX_IDS = (
    '9606',  # Human
    '10090',  # Mouse
    '10116',  # Rat
    '7227',  # Drosophila
    '4932',  # Yeast
    '7955',  # ZebraFish
    '6239',  # Caenorhabditis elegans
)
SPECIES_CONSORTIUM_MAPPING = {
    '9606': 'HGNC',
    '10090': 'MGI',
    '10116': 'RGD',
    '7227': 'FLYBASE',
    '4932': 'SGD',
    '7955': 'ZFIN',
    '6239': 'WB',
}

#: All namepace codes (in lowercase) that can map to ncbigene
CONSORTIUM_SPECIES_MAPPING = {
    database_code: taxonomy_id
    for taxonomy_id, database_code in SPECIES_CONSORTIUM_MAPPING.items()
}

VALID_ENTREZ_NAMESPACES = {'egid', 'eg', 'entrez', 'ncbigene'}
VALID_MGI_NAMESPACES = {'mgi', 'mgd'}
