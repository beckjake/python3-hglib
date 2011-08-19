import common

class test_annotate(common.basetest):
    def test_basic(self):
        self.append('a', 'a\n')
        rev, node0 = self.client.commit('first', addremove=True)
        self.append('a', 'a\n')
        rev, node1 = self.client.commit('second')

        self.assertEquals(list(self.client.annotate('a')), [('0', 'a'), ('1', 'a')])
        self.assertEquals(list(self.client.annotate('a', user=True, file=True,
                          number=True, changeset=True, line=True, verbose=True)),
                          [('test 0 %s a:1' % node0[:12], 'a'),
                           ('test 1 %s a:2' % node1[:12], 'a')])

    def test_files(self):
        self.append('a', 'a\n')
        rev, node0 = self.client.commit('first', addremove=True)
        self.append('b', 'b\n')
        rev, node1 = self.client.commit('second', addremove=True)
        self.assertEquals(list(self.client.annotate(['a', 'b'])),
                          [('0', 'a'), ('1', 'b')])

    def test_two_colons(self):
        self.append('a', 'a: b\n')
        self.client.commit('first', addremove=True)
        self.assertEquals(list(self.client.annotate('a')), [('0', 'a: b')])
