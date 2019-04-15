# -*- coding: utf-8 -*-

"""A Bio2BEL package for Entrez Gene and HomoloGene."""

from .homologene_manager import Manager as HomologeneManager  # noqa: F401
from .manager import Manager  # noqa: F401

__version__ = '0.2.2-dev'

__title__ = 'bio2bel_entrez'
__description__ = "A package for parsing and storing Entrez Gene"
__url__ = 'https://github.com/cthoyt/pyentrez'

__author__ = 'Charles Tapley Hoyt'
__email__ = 'charles.hoyt@scai.fraunhofer.de'

__license__ = 'MIT License'
__copyright__ = 'Copyright (c) 2017-2018 Charles Tapley Hoyt'
