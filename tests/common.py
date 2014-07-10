import os
import sys
import tempfile
import shutil
import unittest

import hglib
client = hglib.client

def resultappender(lst):
    def decorator(f):
        def decorated(*args, **kwargs):
            lst.append(args[0])
            return f(*args, **kwargs)
        return decorated
    return decorator

class basetest(unittest.TestCase):
    def setUp(self):
        self._testtmp = os.environ["TESTTMP"] = os.environ["HOME"] = \
            os.path.join(os.environ["HGTMP"], self.__class__.__name__)

        self.clients = []
        self._oldopen = hglib.client.hgclient.open
        # hglib.open = resultappender(self.clients)(hglib.open)
        hglib.client.hgclient.open = resultappender(self.clients)(hglib.client.hgclient.open)

        os.mkdir(self._testtmp)
        os.chdir(self._testtmp)
        # until we can run norepo commands in the cmdserver
        os.system('hg init')
        self.client = hglib.open()

    def tearDown(self):
        # on Windows we cannot rmtree before closing all instances because of used
        # files
        hglib.client.hgclient.open = self._oldopen
        for client in self.clients:
            if client.server is not None:
                client.close()
        os.chdir('..')
        try:
            shutil.rmtree(self._testtmp)
        except AttributeError:
            pass # if our setUp was overriden

    def append(self, path, *args):
        f = open(path, 'ab')
        for a in args:
            if isinstance(a, str):
                a = a.encode('latin-1')
            f.write(a)
        f.close()
