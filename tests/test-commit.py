import common, hglib

class test_commit(common.basetest):
    def test_user(self):
        self.append('a', 'a')
        rev, node = self.client.commit('first', addremove=True, user='foo')
        rev = self.client.log(node)[0]
        self.assertEquals(rev.author, 'foo')

    def test_no_user(self):
        self.append('a', 'a')
        self.assertRaises(hglib.error.CommandError, self.client.commit, 'first', user='')

    def test_close_branch(self):
        self.append('a', 'a')
        rev0, node0 = self.client.commit('first', addremove=True)
        self.client.branch('foo')
        self.append('a', 'a')
        rev1, node1 = self.client.commit('second')
        revclose = self.client.commit('closing foo', closebranch=True)
        rev0, rev1, revclose = self.client.log([node0, node1, revclose[1]])

        self.assertEquals(self.client.branches(),
                          [(rev0.branch, int(rev0.rev), rev0.node[:12])])

        self.assertEquals(self.client.branches(closed=True),
                          [(revclose.branch, int(revclose.rev), revclose.node[:12]),
                           (rev0.branch, int(rev0.rev), rev0.node[:12])])

    def test_message_logfile(self):
        self.assertRaises(ValueError, self.client.commit, 'foo', logfile='bar')
        self.assertRaises(ValueError, self.client.commit)
