import common, os

class test_move(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        self.client.add('a')
        self.assertTrue(self.client.move('a', 'b'))

    # hg returns 0 even if there were warnings
    #def test_warnings(self):
    #    self.append('a', 'a')
    #    self.client.add('a')
    #    os.mkdir('c')
    #    self.assertFalse(self.client.move(['a', 'b'], 'c'))
