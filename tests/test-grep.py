import common

class test_grep(common.basetest):
    def test_basic(self):
        self.append('a', 'a\n')
        self.append('b', 'ab\n')
        self.client.commit('first', addremove=True)

        # no match
        self.assertEquals(list(self.client.grep('c')), [])

        self.assertEquals(list(self.client.grep('a')),
                          [('a', '0', 'a'), ('b', '0', 'ab')])
        self.assertEquals(list(self.client.grep('a', 'a')), [('a', '0', 'a')])

        self.assertEquals(list(self.client.grep('b')), [('b', '0', 'ab')])

    def test_options(self):
        self.append('a', 'a\n')
        self.append('b', 'ab\n')
        rev, node = self.client.commit('first', addremove=True)

        self.assertEquals([('a', '0', '+', 'a'), ('b', '0', '+', 'ab')],
                          list(self.client.grep('a', all=True)))

        self.assertEquals([('a', '0'), ('b', '0')],
                          list(self.client.grep('a', fileswithmatches=True)))

        self.assertEquals([('a', '0', '1', 'a'), ('b', '0', '1', 'ab')],
                          list(self.client.grep('a', line=True)))

        self.assertEquals([('a', '0', 'test', 'a'), ('b', '0', 'test', 'ab')],
                          list(self.client.grep('a', user=True)))

        self.assertEquals([('a', '0', '1', '+', 'test'),
                           ('b', '0', '1', '+', 'test')],
                          list(self.client.grep('a', all=True, user=True, line=True,
                                                fileswithmatches=True)))
