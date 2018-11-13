# -*- coding: utf-8 -*-

"""Tests for enrichment functions."""

from itertools import chain

from bio2bel_entrez.constants import MODULE_NAME, VALID_ENTREZ_NAMESPACES
from pybel import BELGraph
from pybel.dsl import gene
from tests.cases import PopulatedDatabaseMixin

rgd_gene_symbol = 'Mapk1'
rgd_node = gene(namespace='RGD', name=rgd_gene_symbol)
rat_entrez_id = '116590'
rat_entrez_node = gene(namespace=MODULE_NAME, name=rgd_gene_symbol, identifier='116590')

hgnc_gene_symbol = 'MAPK1'
hgnc_node = gene(namespace='HGNC', name=hgnc_gene_symbol)
human_entrez_id = '5594'
human_entrez_node = gene(namespace=MODULE_NAME, name=hgnc_gene_symbol, identifier='5594')

entrez_namespaces = list(chain(
    VALID_ENTREZ_NAMESPACES,
    map(lambda s: s.upper(), VALID_ENTREZ_NAMESPACES),
))


class TestOrthologs(PopulatedDatabaseMixin):
    """Test loading of orthologs."""

    def test_populated(self):
        """Test the database is populated."""
        self.assertEqual(3, self.manager.count_genes())
        self.assertEqual(3, self.manager.count_species())
        self.assertEqual(1, self.manager.count_homologenes())

    def test_get_rgd(self):
        """Test getting a gene by RGD gene symbol."""
        node = self.manager.get_gene_by_rgd_name(rgd_gene_symbol)
        self.assertIsNotNone(node)
        self.assertEqual('116590', node.entrez_id)

    def test_get_hgnc(self):
        """Test getting a gene by HGNC gene symbol."""
        node = self.manager.get_gene_by_hgnc_name(hgnc_gene_symbol)
        self.assertIsNotNone(node)
        self.assertEqual('5594', node.entrez_id)

    def test_enrich_equivalencies_hgnc(self):
        """Test adding equivalences to an HGNC node."""
        graph = BELGraph()
        graph.add_node_from_data(hgnc_node)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        # test iterating over the genes
        genes = list(self.manager.iter_genes(graph))
        self.assertEqual(1, len(genes), msg='missing genes')

        self.manager.enrich_equivalences(graph)

        self.assertIn(human_entrez_node, graph, msg=f'missing human entrez node. Has: {graph.nodes()}')
        self.assertIn(human_entrez_node, graph[hgnc_node])
        self.assertIn(hgnc_node, graph[human_entrez_node])

    def test_enrich_equivalencies_rgd(self):
        """Test adding equivalences to an RGD node."""
        graph = BELGraph()
        graph.add_node_from_data(rgd_node)

        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        self.manager.enrich_equivalences(graph)

        self.assertIn(rat_entrez_node, graph)
        self.assertIn(rat_entrez_node, graph[rgd_node])
        self.assertIn(rgd_node, graph[rat_entrez_node])

    def help_test_enrich_orthologs_on_rgd(self, graph, rat_node):
        """Help test enriching orthologs on an RGD node."""
        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        self.manager.enrich_orthologies(graph)

        self.assertLess(1, graph.number_of_nodes())
        self.assertLess(0, graph.number_of_edges())

        self.assertIn(human_entrez_node, graph, msg=f'Missing human node. Graph has: {graph.nodes()}')
        self.assertIn(rat_node, graph[human_entrez_node])

    def test_enrich_orthologs_on_rgd_symbol(self):
        """Test enriching a graph that contains an RGD node identified by Entrez."""
        # Test that if there's a name and identifier that the name gets thrown away
        for entrez_namespace in entrez_namespaces:
            graph = BELGraph()
            rat_node = gene(namespace=entrez_namespace, name=rgd_gene_symbol, identifier='116590')
            graph.add_node_from_data(rat_node)
            self.help_test_enrich_orthologs_on_rgd(graph, rat_node)

        # Test the case when there's no name
        for entrez_namespace in entrez_namespaces:
            graph = BELGraph()
            rat_node = gene(namespace=entrez_namespace, identifier='116590')
            graph.add_node_from_data(rat_node)
            self.help_test_enrich_orthologs_on_rgd(graph, rat_node)

    def help_test_enrich_orthologs_on_hgnc(self, graph, human_node):
        """Help test enriching orthologs on an HGNC node."""
        self.assertEqual(1, graph.number_of_nodes())
        self.assertEqual(0, graph.number_of_edges())

        self.manager.enrich_orthologies(graph)

        self.assertLess(1, graph.number_of_nodes())
        self.assertLess(0, graph.number_of_edges())

        self.assertIn(rat_entrez_node, graph)
        self.assertIn(rat_entrez_node, graph[human_node])

    def test_enrich_orthologs_on_entrez(self):
        """Test enriching a graph that contains an HGNC node identified by Entrez."""
        for namespace in entrez_namespaces:
            graph = BELGraph()
            node = gene(namespace=namespace, name=hgnc_gene_symbol, identifier='5594')
            graph.add_node_from_data(node)
            self.help_test_enrich_orthologs_on_hgnc(graph, node)

        for namespace in entrez_namespaces:
            graph = BELGraph()
            node = gene(namespace=namespace, identifier='5594')
            graph.add_node_from_data(node)
            self.help_test_enrich_orthologs_on_hgnc(graph, node)

    def test_enrich_orthologs_on_hgnc(self):
        """Test enriching orthologs on an HGNC node."""
        graph = BELGraph()
        graph.add_node_from_data(hgnc_node)
        self.help_test_enrich_orthologs_on_hgnc(graph, hgnc_node)
