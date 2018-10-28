# -*- coding: utf-8 -*-

"""Test cases for Bio2BEL Entrez."""

from bio2bel.testing import AbstractTemporaryCacheClassMixin
from bio2bel_entrez import Manager
from tests.constants import TEST_GENE_INFO_PATH, TEST_HOMOLOGENE_PATH


class PopulatedDatabaseMixin(AbstractTemporaryCacheClassMixin):
    """A test case with a populated database."""

    Manager = Manager

    @classmethod
    def populate(cls):
        """Populate the database with Entrez."""
        cls.manager.populate(
            gene_info_url=TEST_GENE_INFO_PATH,
            homologene_url=TEST_HOMOLOGENE_PATH,
        )
