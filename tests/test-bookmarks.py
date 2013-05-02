import common

class test_bookmarks(common.basetest):
    def test_empty(self):
        self.assertEquals(self.client.bookmarks(), ([], -1))

    def test_basic(self):
        self.append('a', 'a')
        rev0, node0 = self.client.commit('first', addremove=True)
        self.append('a', 'a')
        rev1, node1 = self.client.commit('second')

        self.client.bookmark('zero', rev0)
        self.assertEquals(self.client.bookmarks(),
                          ([('zero', rev0, node0[:12])], -1))

        self.client.bookmark('one', rev1)
        self.assertEquals(self.client.bookmarks(),
                          ([('one', rev1, node1[:12]),
                            ('zero', rev0, node0[:12])], -1))

    #def test_spaces(self):
    #    self.client.bookmark('s pace', self.rev0)
    #    self.assertEquals(self.client.bookmarks(),
    #                      ([('s pace', 0, self.rev0.node[:12])], -1))
