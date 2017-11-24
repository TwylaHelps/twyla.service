from setuptools import setup

dependencies = []

setup(
    name="twyla.service",
    version="0.0.1",
    author="Twyla Devs",
    author_email="dev@twylahelps.com",
    description=("Twyla Service Tools"),
    install_requires=dependencies,
    extras_require={
        'test': ['pytest'],
    },
    packages=["twyla.service"],
    entry_points={},
    url="https://bitbucket.org/twyla/twyla.service",
)
