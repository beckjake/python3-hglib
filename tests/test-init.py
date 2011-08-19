import hglib, common, shutil

class test_init(common.basetest):
    def test_exists(self):
        self.assertRaises(hglib.error.CommandError, hglib.init)

    def test_basic(self):
        self.client.close()
        self.client = None
        shutil.rmtree('.hg')

        self.client = hglib.init()
        self.assertTrue(self.client.root().endswith('test_init'))
