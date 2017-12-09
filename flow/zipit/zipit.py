#!/usr/bin/python
# zipit.py

import tarfile

import flow.utils.commons as commons

from flow.artifactstorage.artifactory.artifactory import ArtiFactory


class ZipIt:
    clazz = 'ZipIt'

    def __init__(self, mode, name, contents):
        method = '__init__'
        commons.printMSG(ZipIt.clazz, method, 'begin')

        ZipIt.file_name = name

        if mode == 'artifactory':
            ZipIt.zip_contents = contents
            self._zip_it(name, contents)
            self._ship_it_artifactory(name)

        commons.printMSG(ZipIt.clazz, method, 'end')

    def _zip_it(self, name, contents):
        method = '_zip_it'
        commons.printMSG(ZipIt.clazz, method, 'begin')

        file_with_path = name.split('/')

        try:
            with tarfile.open(file_with_path[-1], 'w') as tar:
                tar.add(contents, name)
        except FileNotFoundError as e:
            commons.printMSG(ArtiFactory.clazz, method, "Could not locate files to zip. {}".format(e), 'ERROR')
            exit(1)
        except Exception as e:
            commons.printMSG(ArtiFactory.clazz, method, "Failure during zip process:  {}".format(e), 'ERROR')
            exit(1)

        commons.printMSG(ZipIt.clazz, method, 'end')

    def _ship_it_artifactory(self, name):
        method = '_ship_it_artifactory'
        commons.printMSG(ZipIt.clazz, method, 'begin')

        file_with_path = name.split('/')

        ar = ArtiFactory()
        ar.publish(file_with_path[-1], name)

        commons.printMSG(ZipIt.clazz, method, 'end')
