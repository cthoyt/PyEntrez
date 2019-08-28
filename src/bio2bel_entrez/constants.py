# -*- coding: utf-8 -*-

"""Constants for Bio2BEL Entrez."""

import os

from bio2bel import get_data_dir

MODULE_NAME = 'ncbigene'
DATA_DIR = get_data_dir(MODULE_NAME)

GENE_INFO_URL = 'ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene_info.gz'
GENE2REFSEQ_URL = 'ftp://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2refseq.gz'
GENE_INFO_DATA_PATH = os.path.join(DATA_DIR, 'gene_info.gz')
GENE2REFSEQ_DATA_PATH = os.path.join(DATA_DIR, 'gene2refseq.gz')
GENE2REFSEQ_HUMAN_DATA_PATH = os.path.join(DATA_DIR, 'gene2refseq.human')
GENE2REFSEQ_HUMAN_SLIM_DATA_PATH = os.path.join(DATA_DIR, 'gene2refseq.human.slim')
HOMOLOGENE_DATA_PATH = os.path.join(DATA_DIR, 'homologene.data')

#: Columns fro gene_info.gz that are used
GENE_INFO_COLUMNS = [
    '#tax_id',
    'GeneID',
    'Symbol',
    'dbXrefs',
    'description',
    'type_of_gene',
]

HOMOLOGENE_BUILD_URL = 'ftp://ftp.ncbi.nih.gov/pub/HomoloGene/current/RELEASE_NUMBER'
HOMOLOGENE_URL = 'ftp://ftp.ncbi.nih.gov/pub/HomoloGene/current/homologene.data'

HOMOLOGENE_COLUMNS = [
    'homologene_id',
    'tax_id',
    'gene_id',
    'gene_symbol',
    'protein_gi',
    'protein_accession',
]

DEFAULT_TAX_IDS = (
    '9606',  # Human
    '10090',  # Mouse
    '10116',  # Rat
    '7227',  # Drosophila
    '4932',  # Yeast
    '6239',  # C. Elegans
    '7955',  # Zebrafish
    '9913',  # Cow
    '9615',  # Dog
)
SPECIES_CONSORTIUM_MAPPING = {
    '10090': 'MGI',  # Mouse
    '10116': 'RGD',  # Rat
    '4932': 'SGD',  # Yeast
    '7227': 'FLYBASE',  # Drosophila
    '9606': 'HGNC',  # Human
    '6239': 'WORMBASE',  # C. Elegans
    '7955': 'ZFIN',  # Zebrafish
}

#: All namepace codes (in lowercase) that can map to ncbigene
CONSORTIUM_SPECIES_MAPPING = {
    database_code: taxonomy_id
    for taxonomy_id, database_code in SPECIES_CONSORTIUM_MAPPING.items()
}

VALID_ENTREZ_NAMESPACES = {'egid', 'eg', 'entrez', 'ncbigene'}
VALID_MGI_NAMESPACES = {'mgi', 'mgd'}

ENCODING = {
    'protein-coding': 'GRP',
    'miscRNA': 'GR',
    'ncRNA': 'GR',
    'snoRNA': 'GR',
    'snRNA': 'GR',
    'tRNA': 'GR',
    'scRNA': 'GR',
    'other': 'G',
    'pseudo': 'GR',
    'unknown': 'GRP',
    'rRNA': 'GR',
}

GENE2REFSEQ_HEADER = [
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

GENE2REFSEQ_COLUMNS = [
    '#tax_id',
    'GeneID',
    # 'status',
    # 'RNA_nucleotide_accession.version',
    # 'RNA_nucleotide_gi',
    # 'protein_accession.version',
    # 'protein_gi',
    # 'genomic_nucleotide_accession.version',
    # 'genomic_nucleotide_gi',
    'start_position_on_the_genomic_accession',
    'end_position_on_the_genomic_accession',
    # 'orientation',
    'assembly',
    # 'mature_peptide_accession.version',
    # 'mature_peptide_gi',
    'Symbol',
]
