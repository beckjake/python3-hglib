import common
import hglib

class test_branch(common.basetest):
    def test_empty(self):
        self.assertEquals(self.client.branch(), 'default')

    def test_basic(self):
        self.assertEquals(self.client.branch('foo'), 'foo')
        self.append('a', 'a')
        rev, node = self.client.commit('first', addremove=True)

        rev = self.client.log(node)[0]

        self.assertEquals(rev.branch, 'foo')
        self.assertEquals(self.client.branches(),
                          [(rev.branch, int(rev.rev), rev.node[:12])])

    def test_reset_with_name(self):
        self.assertRaises(ValueError, self.client.branch, 'foo', clean=True)

    def test_reset(self):
        self.client.branch('foo')
        self.assertEquals(self.client.branch(clean=True), 'default')

    def test_exists(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)
        self.client.branch('foo')
        self.append('a', 'a')
        self.client.commit('second')
        self.assertRaises(hglib.error.CommandError, self.client.branch, 'default')

    def test_force(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)
        self.client.branch('foo')
        self.append('a', 'a')
        self.client.commit('second')

        self.assertRaises(hglib.error.CommandError, self.client.branch, 'default')
        self.assertEquals(self.client.branch('default', force=True), 'default')
