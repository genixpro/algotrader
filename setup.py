import os

from setuptools import setup, find_packages
from Cython.Build import cythonize

here = os.path.abspath(os.path.dirname(__file__))
with open('requirements.txt', 'rt') as f:
    requires = f.readlines()

tests_require = [

]

setup(
    name='algotrader',
    version='0.0',
    description="A library that implements an options pricing and trading algorithm",
    long_description="",
    classifiers=[
        'Programming Language :: Python',
    ],
    author='',
    author_email='',
    url='',
    keywords='algorithmic trading options derivatives markets',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    package_data={
        'algotrader': [

        ]
    },
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'algotrader_download_latest_data = algotrader.bin.download_latest_data:run',
            'algotrader_analyze_options = algotrader.bin.analyze_options:run',
            'algotrader_optimize_model = algotrader.bin.optimize_model:run',
        ]
    },
    ext_modules=cythonize("algotrader/simulation.pyx"),
)

