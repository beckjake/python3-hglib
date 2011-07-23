import common
import hglib

class test_outgoing_incoming(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)
        self.append('a', 'a')
        self.client.commit('second')

        self.client.clone(dest='bar')
        bar = hglib.open('bar')

        self.assertEquals(self.client.log(), bar.log())
        self.assertEquals(self.client.outgoing(path='bar'), bar.incoming())

        self.append('a', 'a')
        rev = self.client.commit('third')
        out = self.client.outgoing(path='bar')

        self.assertEquals(len(out), 1)
        self.assertEquals(out[0], rev)

        self.assertEquals(out, bar.incoming())
