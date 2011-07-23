#!/usr/bin/env python

import unittest

import sys, os, subprocess, cStringIO, shutil, tempfile

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')
import hglib

class test_hglib(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        os.chdir(self._tmpdir)
        # until we can run norepo commands in the cmdserver
        os.system('hg init')
        self.client = hglib.open()

    def tearDown(self):
        shutil.rmtree(self._tmpdir)

    def append(self, path, *args):
        f = open(path, 'a')
        for a in args:
            f.write(str(a))
        f.close()

    def test_log(self):
        self.append('a', 'a')
        rev0 = self.client.commit('first', addremove=True)
        self.append('a', 'a')
        rev1 = self.client.commit('second')

        revs = self.client.log()
        revs.reverse()

        self.assertTrue(len(revs) == 2)
        self.assertEquals(revs[1], rev1)

        self.assertEquals(revs[0], self.client.log('0')[0])

    def test_outgoing_incoming(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)
        self.append('a', 'a')
        self.client.commit('second')

        self.client.clone(dest='bar')
        bar = hglib.open('bar')

        self.assertEquals(self.client.log(), bar.log())
        self.assertEquals(self.client.outgoing(path='bar'), bar.incoming())

        self.append('a', 'a')
        rev = self.client.commit('third')
        out = self.client.outgoing(path='bar')

        self.assertEquals(len(out), 1)
        self.assertEquals(out[0], rev)

        self.assertEquals(out, bar.incoming())

    def test_branch(self):
        self.assertEquals(self.client.branch(), 'default')
        self.append('a', 'a')
        rev = self.client.commit('first', addremove=True)
        branches = self.client.branches()

        self.assertEquals(rev, branches[rev.branch])

    def test_encoding(self):
        self.client = hglib.open(encoding='utf-8')
        self.assertEquals(self.client.encoding, 'utf-8')

    def test_paths(self):
        open('.hg/hgrc', 'a').write('[paths]\nfoo = bar\n')

        # hgrc isn't watched for changes yet, have to reconnect
        self.client = hglib.open()
        paths = self.client.paths()
        self.assertEquals(len(paths), 1)
        self.assertEquals(paths['foo'], os.path.abspath('bar'))
        self.assertEquals(self.client.paths('foo'), os.path.abspath('bar'))

    def test_import(self):
        patch = """
# HG changeset patch
# User test
# Date 0 0
# Node ID c103a3dec114d882c98382d684d8af798d09d857
# Parent  0000000000000000000000000000000000000000
1

diff -r 000000000000 -r c103a3dec114 a
--- /dev/null	Thu Jan 01 00:00:00 1970 +0000
+++ b/a	Thu Jan 01 00:00:00 1970 +0000
@@ -0,0 +1,1 @@
+1
"""
        self.client.import_(cStringIO.StringIO(patch))
        self.assertEquals(self.client.cat(['a']), '1\n')

if __name__ == '__main__':
    stream = cStringIO.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=0)

    # XXX fix this
    module = __import__('__main__')
    loader = unittest.TestLoader()
    ret = not runner.run(loader.loadTestsFromModule(module)).wasSuccessful()
    if ret:
        print stream.getvalue()

    sys.exit(ret)
