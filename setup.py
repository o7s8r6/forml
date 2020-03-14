"""
Setuptools script for ForML package.
"""
import sys

import setuptools

sys.path.insert(0, 'src')
import forml  # noqa: E402

EXTRAS_STDLIB = {
    'pandas',
    'scikit-learn'
}

EXTRAS_GRAPHVIZ = {
    'graphviz'
}

EXTRAS_DASK = {
    'dask',
    'cloudpickle'
}

EXTRAS_DOC = {
    'sphinx'
}

EXTRAS_DEV = {
    'pre-commit',
    'flake8',
    'mypy'
}

EXTRAS_ALL = EXTRAS_STDLIB | EXTRAS_GRAPHVIZ | EXTRAS_DASK | EXTRAS_DEV | EXTRAS_DOC

setuptools.setup(name='forml',
                 version=forml.__version__,
                 description='Lifecycle management framework for Data science projects',
                 long_description=open('README.md', 'r').read(),
                 long_description_content_type='text/markdown',
                 url='https://github.com/formlio/forml',
                 author='ForML Authors',
                 author_email='noreply@forml.io',
                 license='Apache License 2.0',
                 packages=setuptools.find_packages(where='src'),
                 package_dir={'': 'src'},
                 package_data={'forml.conf': ['*.ini']},
                 setup_requires=['pytest-runner', 'pytest-pylint', 'pytest-flake8'],
                 tests_require=['pytest-cov', 'pylint', 'pytest'],
                 install_requires=['joblib', 'pip', 'setuptools', 'packaging>=20.0'],
                 extras_require={
                     'all': EXTRAS_ALL,
                     'dev': EXTRAS_DEV,
                     'doc': EXTRAS_DOC,
                     'stdlib': EXTRAS_STDLIB,
                     'graphviz': EXTRAS_GRAPHVIZ,
                     'dask': EXTRAS_DASK
                 },
                 entry_points={'console_scripts': [
                     'forml = forml.cli.forml:Parser',
                 ]},
                 python_requires='>=3.6',
                 classifiers=[
                     'Development Status :: 2 - Pre-Alpha',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'Intended Audience :: Science/Research',
                     'License :: Other/Proprietary License',
                     'Programming Language :: Python :: 3',
                     'Topic :: Scientific/Engineering :: Artificial Intelligence',
                     'Topic :: System :: Distributed Computing'
                 ],
                 zip_safe=False)
