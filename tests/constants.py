# -*- coding: utf-8 -*-

import logging
import os
import tempfile
import unittest

from bio2bel_entrez import Manager

log = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
gene_info_test_path = os.path.join(dir_path, 'gene_info')
homologene_test_path = os.path.join(dir_path, 'homologene.data')


class TemporaryCacheClsMixin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Creates a temporary file to use as a persistent database throughout tests in this class. Subclasses of
        :class:`TemporaryCacheClsMixin` can extend :func:`TemporaryCacheClsMixin.setUpClass` to populate the database
        """
        cls.fd, cls.path = tempfile.mkstemp()
        cls.connection = 'sqlite:///' + cls.path
        log.info('test database at %s', cls.connection)
        cls.manager = Manager(connection=cls.connection)

    @classmethod
    def tearDownClass(cls):
        """Closes the connection to the database and removes the files created for it"""
        cls.manager.session.close()
        os.close(cls.fd)
        os.remove(cls.path)


class PopulatedDatabaseMixin(TemporaryCacheClsMixin):
    @classmethod
    def setUpClass(cls):
        """Creates a persistent database and populates it with the test data included in the Bio2BEL Entrez repository
        """
        super(PopulatedDatabaseMixin, cls).setUpClass()
        cls.manager.populate(
            gene_info_url=gene_info_test_path,
            homologene_url=homologene_test_path
        )

    @classmethod
    def tearDownClass(cls):
        """Drops everything from the persistent database before tearing it down"""
        cls.manager.drop_all()
        super(PopulatedDatabaseMixin, cls).tearDownClass()
