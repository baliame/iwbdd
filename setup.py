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
        "pygame",
        "numpy",
        "pyopengl",
        "pillow",
        "glfw"
    ],
    entry_points={
        'console_scripts': [
            'iwbdd=iwbdd.iwbdd:main',
            'iwbdd_prof=iwbdd.iwbdd:profiled',
            'iwbdd_profed=iwbdd.iwbdd:profiled_ed',
            'iwbdd_tsp=iwbdd.iwbdd:pack_tilesets',
            'iwbdd_bgp=iwbdd.iwbdd:pack_backgrounds',
            'iwbdd_ssp=iwbdd.iwbdd:pack_spritesheets',
            'iwbdd_adp=iwbdd.iwbdd:pack_audio',
            'iwbdd_ogl=iwbdd.iwbdd:opengl_tests_main',
            'iwbdd_editor=iwbdd.iwbdd:editor',
        ],
        'gui_scripts': [
            'iwbdd_boss=iwbdd.iwbdd:boss_tester',
            'iwbdd_bossprof=iwbdd.iwbdd:profiled_boss',
            'iwbdd_editor_w2=iwbdd.iwbdd:editor_w2',
            'iwbdd_editor_scaled=iwbdd.iwbdd:editor_scaled',
        ],
    }
)
