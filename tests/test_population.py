# -*- coding: utf-8 -*-

import unittest

from tests.constants import PopulatedDatabaseMixin


class TestPopulation(PopulatedDatabaseMixin):
    def test_populated(self):
        self.assertEqual(3, self.manager.count_genes())
        self.assertEqual(3, self.manager.count_species())
        self.assertEqual(1, self.manager.count_homologenes())


if __name__ == '__main__':
    unittest.main()
