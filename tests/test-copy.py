import common
import hglib

class test_copy(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)

        self.assertTrue(self.client.copy('a', 'b'))
        self.assertEquals(self.client.status(), [('A', 'b')])
        self.append('c', 'a')
        self.assertTrue(self.client.copy('a', 'c', after=True))
        self.assertEquals(self.client.status(), [('A', 'b'), ('A', 'c')])

    # hg returns 0 even if there were warnings
    #def test_warnings(self):
    #    self.append('a', 'a')
    #    self.client.commit('first', addremove=True)

    #    self.assertTrue(self.client.copy('a', 'b'))
    #    self.assertFalse(self.client.copy('a', 'b'))
