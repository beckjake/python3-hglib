import common, os
import hglib

class test_paths(common.basetest):
    def test_basic(self):
        f = open('.hg/hgrc', 'a')
        f.write('[paths]\nfoo = bar\n')
        f.close()

        # hgrc isn't watched for changes yet, have to reopen
        self.client = hglib.open()
        paths = self.client.paths()
        self.assertEquals(len(paths), 1)
        self.assertEquals(paths['foo'], os.path.abspath('bar'))
        self.assertEquals(self.client.paths('foo'), os.path.abspath('bar'))
