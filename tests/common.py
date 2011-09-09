import os, sys, tempfile, shutil
import unittest

import hglib

def resultappender(list):
    def decorator(f):
        def decorated(*args, **kwargs):
            result = f(*args, **kwargs)
            list.append(result)
            return result
        return decorated
    return decorator

class basetest(unittest.TestCase):
    def setUp(self):
        self._testtmp = os.environ["TESTTMP"] = os.environ["HOME"] = \
            os.path.join(os.environ["HGTMP"], self.__class__.__name__)

        self.clients = []
        self._oldopen = hglib.open
        hglib.open = resultappender(self.clients)(hglib.open)

        os.mkdir(self._testtmp)
        os.chdir(self._testtmp)
        # until we can run norepo commands in the cmdserver
        os.system('hg init')
        self.client = hglib.open()

    def tearDown(self):
        # on Windows we cannot rmtree before closing all instances because of used
        # files
        hglib.open = self._oldopen
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
            f.write(str(a))
        f.close()
