import common, hglib

class test_pull(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)

        self.client.clone(dest='other')
        other = hglib.open('other')

        self.append('a', 'a')
        self.client.commit('second')

        self.assertTrue(other.pull())
        self.assertEquals(self.client.log(), other.log())

    def test_unresolved(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)

        self.client.clone(dest='other')
        other = hglib.open('other')

        self.append('a', 'a')
        self.client.commit('second')

        self.append('other/a', 'b')
        self.assertFalse(other.pull(update=True))
        self.assertTrue(('M', 'a') in other.status())
