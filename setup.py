# coding: utf-8

from distutils.core import setup

setup(
    name='django-electron-pdf',
    packages=['electron_pdf'],
    version='0.1',
    description='A Django wrapper to generate PDF from URL, HTML or Markdown files.',
    author='Madis Väin',
    author_email='madisvain@gmail.com',
    url='https://github.com/namespace-ee/django-electron-pdf',
    download_url='https://github.com/namespace-ee/django-electron-pdf/tarball/0.1',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
