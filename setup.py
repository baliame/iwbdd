from setuptools import *

description = 'IWBDD'

setup(
    name='iwbdd',
    version='1.0.0',
    description=description,
    long_description=description,
    url='https://github.com/baliame/iwbdd',
    author='Baliame',
    author_email='akos.toth@cheppers.com',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(),
    install_requires=[
        "pygame"
    ],
    entry_points={
        'console_scripts': [
            'iwbdd_tsp=iwbdd.iwbdd:pack_tilesets',
            'iwbdd_bgp=iwbdd.iwbdd:pack_backgrounds',
            'iwbdd_ssp=iwbdd.iwbdd:pack_spritesheets'
        ],
        'gui_scripts': [
            'iwbdd=iwbdd.iwbdd:main',
            'iwbdd_editor=iwbdd.iwbdd:editor'
        ],
    }
)
