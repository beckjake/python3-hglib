from . import common
import hglib

class test_phase(common.basetest):
    """test the different ways to use the phase command"""
    def test_phase(self):
        """test getting data from a single changeset"""
        self.append('a', 'a')
        rev, node0 = self.client.commit('first', addremove=True)
        self.assertEqual([(0, 'draft')], self.client.phase(node0))
        ctx = self.client[rev]
        self.assertEqual('draft', ctx.phase())

    def test_phase_public(self):
        """test phase change from draft to public"""
        self.append('a', 'a')
        rev, node0 = self.client.commit('first', addremove=True)
        self.client.phase(node0, public=True)
        self.assertEqual([(0, 'public')], self.client.phase(node0))
        ctx = self.client[rev]
        self.assertEqual('public', ctx.phase())

    def test_phase_secret(self):
        """test phase change from draft to secret"""
        self.append('a', 'a')
        rev, node0 = self.client.commit('first', addremove=True)
        with self.assertRaises(hglib.error.CommandError):
            self.client.phase(node0, secret=True)
        self.client.phase(node0, secret=True, force=True)
        self.assertEqual([(0, 'secret')], self.client.phase(node0))
        ctx = self.client[rev]
        self.assertEqual('secret', ctx.phase())


    def test_phase_multiple(self):
        """test phase changes and show the phases of the different changesets"""
        self.append('a', 'a')
        rev, node0 = self.client.commit('a', addremove=True)
        self.client.phase(node0, public=True)
        self.append('b', 'b')
        rev, node1 = self.client.commit('b', addremove=True)
        self.append('c', 'c')
        rev, node2 = self.client.commit('c', addremove=True)
        self.client.phase(node2, secret=True, force=True)
        self.assertEqual([(0, 'public'), (2, 'secret'), (1, 'draft')],
                         self.client.phase([node0,node2,node1]))


