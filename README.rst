Bio2BEL Entrez |build| |coverage| |documentation|
=================================================
This package downloads, parses, and stores the Entrez Gene and HomoloGene databases then provides utilities for
converting to BEL.

Installation |pypi_version| |python_versions| |pypi_license|
------------------------------------------------------------
``bio2bel_entrez`` can be installed easily from `PyPI <https://pypi.python.org/pypi/bio2bel_entrez>`_ with
the following code in your favorite terminal:

.. code-block:: sh

    $ python3 -m pip install bio2bel_entrez

or from the latest code on `GitHub <https://github.com/bio2bel/entrez>`_ with:

.. code-block:: sh

    $ python3 -m pip install git+https://github.com/bio2bel/entrez.git@master

Setup
-----
Entrez can be downloaded and populated from either the Python REPL or the automatically installed command line
utility.

Python REPL
~~~~~~~~~~~
.. code-block:: python

    >>> import bio2bel_entrez
    >>> entrez_manager = bio2bel_entrez.Manager()
    >>> entrez_manager.populate()

Command Line Utility
~~~~~~~~~~~~~~~~~~~~
.. code-block:: bash

    bio2bel_entrez populate

Citations
---------
- Maglott, D., *et al.* (2011). `Entrez Gene: gene-centered information at NCBI <http://doi.org/10.1093/nar/gkq1237>`_. Nucleic Acids Research, 39(Database issue), D52–D57.

.. |build| image:: https://travis-ci.org/bio2bel/entrez.svg?branch=master
    :target: https://travis-ci.org/bio2bel/entrez
    :alt: Build Status

.. |coverage| image:: https://codecov.io/gh/bio2bel/entrez/coverage.svg?branch=master
    :target: https://codecov.io/gh/bio2bel/entrez?branch=master
    :alt: Coverage Status

.. |documentation| image:: http://readthedocs.org/projects/bio2bel-entrez/badge/?version=latest
    :target: http://bio2bel.readthedocs.io/projects/entrez/en/latest/?badge=latest
    :alt: Documentation Status

.. |climate| image:: https://codeclimate.com/github/bio2bel/entrez/badges/gpa.svg
    :target: https://codeclimate.com/github/bio2bel/entrez
    :alt: Code Climate

.. |python_versions| image:: https://img.shields.io/pypi/pyversions/bio2bel_entrez.svg
    :alt: Stable Supported Python Versions

.. |pypi_version| image:: https://img.shields.io/pypi/v/bio2bel_entrez.svg
    :alt: Current version on PyPI

.. |pypi_license| image:: https://img.shields.io/pypi/l/bio2bel_entrez.svg
    :alt: MIT License
