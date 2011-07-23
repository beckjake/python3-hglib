import common
import hglib

class test_encoding(common.basetest):
    def test_basic(self):
        self.client = hglib.open(encoding='utf-8')
        self.assertEquals(self.client.encoding, 'utf-8')
