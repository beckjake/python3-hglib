import common
import hglib

class test_log(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        rev0 = self.client.commit('first', addremove=True)
        self.append('a', 'a')
        rev1 = self.client.commit('second')

        revs = self.client.log()
        revs.reverse()

        self.assertTrue(len(revs) == 2)
        self.assertEquals(revs[1], rev1)

        self.assertEquals(revs[0], self.client.log('0')[0])
