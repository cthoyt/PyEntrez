# -*- coding: utf-8 -*-

"""Constants for testing Bio2BEL Entrez."""

import os

__all__ = [
    'TEST_GENE_INFO_PATH',
    'TEST_HOMOLOGENE_PATH',
]

HERE = os.path.dirname(os.path.realpath(__file__))
TEST_GENE_INFO_PATH = os.path.join(HERE, 'gene_info')
TEST_HOMOLOGENE_PATH = os.path.join(HERE, 'homologene.data')
