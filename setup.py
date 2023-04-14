from setuptools import find_packages, setup

setup(
    name='sqlalchemyfilter',
    version='0.0.1',
    description='Filtered/paginated lists on DTO classes using SQLAlchemy',
    author='Rah Henrique',
    author_email='rafael@rah.com.br',
    url='https://github.com/rahenrique/sqlalchemy-filter',
    packages=find_packages(include=['sqlalchemyfilter']),
    license='MIT',
)
