import common
import hglib

class test_outgoing_incoming(common.basetest):
    def test_no_path(self):
        self.assertRaises(hglib.error.CommandError, self.client.incoming)

    def test_empty(self):
        self.client.clone(dest='other')
        self.other = hglib.open('other')

        self.assertEquals(self.other.incoming(), [])
        self.assertEquals(self.other.outgoing(), [])

    def test_basic(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)
        self.append('a', 'a')
        self.client.commit('second')

        self.client.clone(dest='other')
        other = hglib.open('other')

        self.assertEquals(self.client.log(), other.log())
        self.assertEquals(self.client.outgoing(path='other'), other.incoming())

        self.append('a', 'a')
        rev, node = self.client.commit('third')
        out = self.client.outgoing(path='other')

        self.assertEquals(len(out), 1)
        self.assertEquals(out[0].node, node)

        self.assertEquals(out, other.incoming())

    def test_bookmarks(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)
        self.append('a', 'a')
        self.client.commit('second')

        self.client.clone(dest='other')
        other = hglib.open('other')

        self.client.bookmark('bm1', 1)

        self.assertEquals(other.incoming(bookmarks=True),
                          [('bm1', self.client.tip().node[:12])])

        self.assertEquals(self.client.outgoing(path='other', bookmarks=True),
                          [('bm1', self.client.tip().node[:12])])
