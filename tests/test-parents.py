import common

class test_parents(common.basetest):
    def test_noparents(self):
        self.assertEquals(self.client.parents(), None)

    def test_basic(self):
        self.append('a', 'a')
        rev, node = self.client.commit('first', addremove=True)
        self.assertEquals(node, self.client.parents()[0].node)
        self.assertEquals(node, self.client.parents(file='a')[0].node)

    def test_two_parents(self):
        pass
