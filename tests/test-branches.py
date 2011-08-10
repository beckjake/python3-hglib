import common, hglib

class test_branches(common.basetest):
    def test_empty(self):
        self.assertEquals(self.client.branches(), [])

    def test_basic(self):
        self.append('a', 'a')
        rev0 = self.client.commit('first', addremove=True)
        self.client.branch('foo')
        self.append('a', 'a')
        rev1 = self.client.commit('second')
        branches = self.client.branches()

        expected = []
        for r, n in (rev1, rev0):
            r = self.client.log(r)[0]
            expected.append((r.branch, int(r.rev), r.node[:12]))

        self.assertEquals(branches, expected)

    def test_active_closed(self):
        pass
