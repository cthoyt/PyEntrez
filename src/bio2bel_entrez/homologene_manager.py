# -*- coding: utf-8 -*-

"""Manager for Bio2BEL Entrez."""

from bio2bel import AbstractManager
from bio2bel.manager.namespace_manager import BELNamespaceManagerMixin
from pybel.manager.models import Namespace, NamespaceEntry
from .constants import MODULE_NAME
from .models import Base, Homologene

__all__ = [
    'Manager',
]


class Manager(AbstractManager, BELNamespaceManagerMixin):
    """Manages the HomoloGene database."""

    module_name = MODULE_NAME
    namespace_model = Homologene

    identifiers_recommended = 'HomoloGene'
    identifiers_pattern = '^\d+$'
    identifiers_miriam = 'MIR:00000275'
    identifiers_namespace = 'homologene'
    identifiers_url = 'http://identifiers.org/homologene/'

    @staticmethod
    def _get_identifier(model: Homologene) -> str:
        return model.homologene_id

    def _create_namespace_entry_from_model(self, model: Homologene, namespace: Namespace) -> NamespaceEntry:
        pass

    @property
    def _base(self):
        return Base

    def is_populated(self):
        """Check if the database is populated."""
        pass

    def populate(self, *args, **kwargs):
        """Populate the database."""
        pass

    def summarize(self):
        """Summarize the database."""
