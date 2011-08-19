import os, sys, tempfile, shutil
import unittest

import hglib

class basetest(unittest.TestCase):
    def setUp(self):
        self._testtmp = os.environ["TESTTMP"] = os.environ["HOME"] = \
            os.path.join(os.environ["HGTMP"], self.__class__.__name__)

        os.mkdir(self._testtmp)
        os.chdir(self._testtmp)
        # until we can run norepo commands in the cmdserver
        os.system('hg init')
        self.client = hglib.open()

    def tearDown(self):
        try:
            shutil.rmtree(self._testtmp)
        except AttributeError:
            pass # if our setUp was overriden

    def append(self, path, *args):
        f = open(path, 'a')
        for a in args:
            f.write(str(a))
        f.close()
