import common
import hglib

class test_log(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        rev0, node0 = self.client.commit('first', addremove=True)
        self.append('a', 'a')
        rev1, node1 = self.client.commit('second')

        revs = self.client.log()
        revs.reverse()

        self.assertTrue(len(revs) == 2)
        self.assertEquals(revs[1].node, node1)

        self.assertEquals(revs[0], self.client.log('0')[0])
        self.assertEquals(self.client.log(), self.client.log(files=['a']))
