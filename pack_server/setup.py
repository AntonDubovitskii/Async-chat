from setuptools import setup, find_packages

setup(name='server_chat_project_adub',
      version='0.1',
      description='Server packet',
      packages=find_packages(),
      author_email='gtoll@yandex.ru',
      author='Anton Dubovitskii',
      install_requires=['PyQt5 ==5.15.9', 'sqlalchemy ==2.0.15', 'pycryptodome', 'pycryptodomex']
      )
