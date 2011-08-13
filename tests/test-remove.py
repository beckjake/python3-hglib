import common

class test_remove(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)
        self.assertTrue(self.client.remove(['a']))

    def test_warnings(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)
        self.assertFalse(self.client.remove(['a', 'b']))
