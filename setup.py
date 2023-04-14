from setuptools import find_packages, setup

setup(
    name='sqlalchemyfilter',
    packages=find_packages(include=['sqlalchemyfilter']),
    version='0.0.1',
    description='Filtered/paginated lists on DTO classes using SQLAlchemy',
    author='Rah Henrique',
    author_email='rafael@rah.com.br',
    license='MIT',
)
