# -*- coding: utf-8 -*-

import logging
import os

from bio2bel.testing import make_temporary_cache_class_mixin
from bio2bel_entrez import Manager

log = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
gene_info_test_path = os.path.join(dir_path, 'gene_info')
homologene_test_path = os.path.join(dir_path, 'homologene.data')


class PopulatedDatabaseMixin(make_temporary_cache_class_mixin(Manager)):
    @classmethod
    def populate(cls):
        """Creates a persistent database and populates it with the test data included in the Bio2BEL Entrez repository
        """
        cls.manager.populate(
            gene_info_url=gene_info_test_path,
            homologene_url=homologene_test_path
        )
