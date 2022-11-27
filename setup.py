from setuptools import setup, find_packages


setup(
    name="resticrc",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["click>=7.0", "attrs>=19.1.0", "pluggy>=0.12.0", "pyyaml>=5.1.2"],
    tests_require=["pytest>=5.1.1", "pytest-mock>=1.10.4", "pytest-cov>=2.7.1"],
    entry_points="""
        [console_scripts]
        resticrc=resticrc.console:cli
    """,
)
