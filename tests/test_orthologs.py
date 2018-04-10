# -*- coding: utf-8 -*-

import unittest

from pybel import BELGraph
from pybel.dsl import gene

from tests.constants import PopulatedDatabaseMixin

rgd_name = 'Mapk1'
rgd_node = gene(namespace='MGI', name=rgd_name)
rat_entrez_id = '116590'
rat_entrez_node = gene(namespace='ENTREZ', identifier='116590')

hgnc_name = 'MAPK1'
hgnc_node = gene(namespace='HGNC', name=hgnc_name)
human_entrez_id = '5594'
human_entrez_node = gene(namespace='ENTREZ', identifier='5594')


class TestOrthologs(PopulatedDatabaseMixin):

    def test_get_rgd(self):
        node = self.manager.get_gene_by_rgd_name(rgd_name)
        self.assertIsNotNone(node)

    def test_get_hgnc(self):
        node = self.manager.get_gene_by_hgnc_name(hgnc_name)
        self.assertIsNotNone(node)

    def test_mgi(self):
        graph = BELGraph()
        graph.add_node_from_data(rgd_node)

        self.manager.enrich_orthologies(graph)

        self.assertIn(rat_entrez_node.as_tuple(), graph)
        self.assertEqual(1, graph.number_of_edges())

        self.assertIn(rat_entrez_node.as_tuple(), graph[rgd_node.as_tuple()])

if __name__ == '__main__':
    unittest.main()