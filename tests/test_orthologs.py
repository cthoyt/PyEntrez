# -*- coding: utf-8 -*-

"""Tests for enrichment functions."""

import unittest
from itertools import chain

from pybel import BELGraph
from pybel.dsl import gene

from bio2bel_entrez.constants import MODULE_NAME
from bio2bel_entrez.manager import VALID_ENTREZ_NAMESPACES
from tests.constants import PopulatedDatabaseMixin

rgd_name = 'Mapk1'
rgd_node = gene(namespace='MGI', name=rgd_name)
rat_entrez_id = '116590'
rat_entrez_node = gene(namespace=MODULE_NAME, name=rgd_name, identifier='116590')

hgnc_gene_symbol = 'MAPK1'
hgnc_node = gene(namespace='HGNC', name=hgnc_gene_symbol)
human_entrez_id = '5594'
human_entrez_node = gene(namespace=MODULE_NAME, name=hgnc_gene_symbol, identifier='5594')


class TestOrthologs(PopulatedDatabaseMixin):
    """Test loading of orthologs."""

    def test_get_rgd(self):
        """Test getting a gene by RGD gene symbol."""
        node = self.manager.get_gene_by_rgd_name(rgd_name)
        self.assertIsNotNone(node)

    def test_get_hgnc(self):
        """Test getting a gene by HGNC gene symbol."""
        node = self.manager.get_gene_by_hgnc_name(hgnc_gene_symbol)
        self.assertIsNotNone(node)

    def help_test_enrich_rgd(self, graph, rat_node):
        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        self.manager.enrich_orthologies(graph)

        self.assertIn(human_entrez_node.as_tuple(), graph, msg='Missing human node. Graph has: {}'.format(list(graph)))
        self.assertIn(rat_node.as_tuple(), graph[human_entrez_node.as_tuple()])

    def test_enrich_rgd_symbol(self):
        """Test enriching a graph that contains a rat node identified by Entrez."""
        namespaces = list(chain(
            VALID_ENTREZ_NAMESPACES,
            map(lambda s: s.upper(), VALID_ENTREZ_NAMESPACES),
        ))

        for namespace in namespaces:
            graph = BELGraph()
            rat_node = gene(namespace=namespace, name=rgd_name, identifier='116590')
            graph.add_node_from_data(rat_node)
            self.help_test_enrich_rgd(graph, rat_node)

        for namespace in namespaces:
            graph = BELGraph()
            rat_node = gene(namespace=namespace, name=rgd_name)
            graph.add_node_from_data(rat_node)
            self.help_test_enrich_rgd(graph, rat_node)

        for namespace in namespaces:
            graph = BELGraph()
            rat_node = gene(namespace=namespace, identifier='116590')
            graph.add_node_from_data(rat_node)
            self.help_test_enrich_rgd(graph, rat_node)

    def test_enrich_hgnc(self):
        graph = BELGraph()
        graph.add_node_from_data(human_entrez_node)
        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        self.manager.enrich_orthologies(graph)

        self.assertIn(rat_entrez_node.as_tuple(), graph)
        self.assertIn(rat_entrez_node.as_tuple(), graph[human_entrez_node.as_tuple()])


if __name__ == '__main__':
    unittest.main()
