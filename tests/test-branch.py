import common
import hglib

class test_branch(common.basetest):
    def test_basic(self):
        self.assertEquals(self.client.branch(), 'default')
        self.append('a', 'a')
        rev = self.client.commit('first', addremove=True)
        branches = self.client.branches()

        self.assertEquals(rev, branches[rev.branch])
