import common, hglib

class test_push(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)

        self.client.clone(dest='other')
        other = hglib.open('other')

        # broken in hg, doesn't return 1 if nothing to push
        #self.assertFalse(self.client.push('other'))

        self.append('a', 'a')
        self.client.commit('second')

        self.assertTrue(self.client.push('other'))
        self.assertEquals(self.client.log(), other.log())
