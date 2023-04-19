from setuptools import find_packages, setup

setup(
    name='SQLAlchemyFilter',
    version='0.0.1',
    description='Filtered/paginated lists on DTO classes using SQLAlchemy',
    author='Rah Henrique',
    author_email='rafael@rah.com.br',
    url='https://github.com/rahenrique/sqlalchemy-filter',
    packages=find_packages(include=['sqlalchemyfilter']),
    install_requires=['SQLAlchemy>=1.4.32'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    license='MIT',
)
