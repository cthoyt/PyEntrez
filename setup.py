# -*- coding: utf-8 -*-

"""Setup.py for Bio2BEL Entrez."""

import codecs
import os
import re

import setuptools

MODULE_NAME = 'entrez'
PACKAGES = setuptools.find_packages(where='src')
META_PATH = os.path.join('src', f'bio2bel_{MODULE_NAME}', '__init__.py')
CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3 :: Only',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Scientific/Engineering :: Bio-Informatics',
    'License :: OSI Approved :: MIT License',
]
INSTALL_REQUIRES = [
    'pybel>=0.14.0,<0.15.0',
    'bio2bel>=0.3.0,<0.4.0',
    'click',
    'pandas',
    'sqlalchemy',
    'six',
    'tqdm',
]
EXTRAS_REQUIRE = {
    'web': [
        'flask',
        'flask_admin',
    ],
    'docs': [
        'flask',
        'flask_admin',
        'sphinx',
        'sphinx-rtd-theme',
        'sphinx-click',
        'sphinx-autodoc-typehints',
    ],
}
ENTRY_POINTS = {
    'bio2bel': [
        'entrez = bio2bel_entrez',
        'homologene = bio2bel_entrez.homologene_manager',
    ],
    'console_scripts': [
        'bio2bel_entrez = bio2bel_entrez.cli:main',
        'bio2bel_homologene = bio2bel_entrez.homologene_manager:main',
    ]
}

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """Build an absolute path from *parts* and return the contents of the resulting file. Assume UTF-8 encoding."""
    with codecs.open(os.path.join(HERE, *parts), 'rb', 'utf-8') as f:
        return f.read()


META_FILE = read(META_PATH)


def find_meta(meta):
    """Extract __*meta*__ from META_FILE."""
    meta_match = re.search(
        r'^__{meta}__ = ["\']([^"\']*)["\']'.format(meta=meta),
        META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError('Unable to find __{meta}__ string'.format(meta=meta))


def get_long_description():
    """Get the long_description from the README.rst file. Assume UTF-8 encoding."""
    with codecs.open(os.path.join(HERE, 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()
    return long_description


if __name__ == '__main__':
    setuptools.setup(
        name=find_meta('title'),
        version=find_meta('version'),
        description=find_meta('description'),
        long_description=get_long_description(),
        url=find_meta('url'),
        author=find_meta('author'),
        author_email=find_meta('email'),
        maintainer=find_meta('author'),
        maintainer_email=find_meta('email'),
        license=find_meta('license'),
        classifiers=CLASSIFIERS,
        packages=PACKAGES,
        package_dir={'': 'src'},
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        entry_points=ENTRY_POINTS,
        zip_safe=False,
    )
