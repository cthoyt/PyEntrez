# -*- coding: utf-8 -*-

"""Manager for Bio2BEL Homologene."""

from bio2bel import AbstractManager
from bio2bel.manager.bel_manager import BELManagerMixin
from bio2bel.manager.namespace_manager import BELNamespaceManagerMixin
from pybel import BELGraph
from pybel.manager.models import Namespace, NamespaceEntry
from .models import Base, Gene, Homologene

__all__ = [
    'Manager',
    'main',
]


class Manager(AbstractManager, BELNamespaceManagerMixin, BELManagerMixin):
    """Gene ortholog group memberships."""

    _base = Base
    module_name = 'homologene'

    namespace_model = Homologene
    has_names = False
    identifiers_recommended = 'HomoloGene'
    identifiers_pattern = r'^\d+$'
    identifiers_miriam = 'MIR:00000275'
    identifiers_namespace = 'homologene'
    identifiers_url = 'http://identifiers.org/homologene/'

    @staticmethod
    def _get_identifier(model: Homologene) -> str:
        return model.homologene_id

    def _create_namespace_entry_from_model(self, model: Homologene, namespace: Namespace) -> NamespaceEntry:
        return NamespaceEntry(
            namespace=namespace,
            name=model.homologene_id,
            identifier=model.homologene_id,
            encoding=model.bel_encoding,
        )

    def is_populated(self) -> bool:
        """Check if the database is populated."""
        return 0 < self.count_homologenes()

    def count_homologenes(self) -> int:
        """Count the number of homologenes in the database."""
        return self._count_model(self.namespace_model)

    def populate(self, *args, **kwargs):
        """Populate the database."""
        raise NotImplementedError

    def summarize(self):
        """Summarize the database."""
        return dict(homologenes=self.count_homologenes())

    def count_relations(self) -> int:
        """Count the number of genes with a HomoloGene."""
        return self.session.query(Gene).filter(Gene.homologene_id.isnot(None)).count()

    def to_bel(self) -> BELGraph:
        """Convert HomoloGene to BEL."""
        graph = BELGraph()
        for homologene, gene in self._get_query(Homologene).join(Gene):
            graph.add_is_a(gene.as_bel(), homologene.as_bel())
        return graph


main = Manager.get_cli()
