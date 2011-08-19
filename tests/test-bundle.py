import common

class test_bundle(common.basetest):
    def test_no_changes(self):
        self.append('a', 'a')
        rev, node0 = self.client.commit('first', addremove=True)
        self.assertFalse(self.client.bundle('bundle', destrepo='.'))

    def test_basic(self):
        self.append('a', 'a')
        rev, node0 = self.client.commit('first', addremove=True)
        self.client.clone(dest='other')

        self.append('a', 'a')
        rev, node1 = self.client.commit('second')

        self.assertTrue(self.client.bundle('bundle', destrepo='other'))
