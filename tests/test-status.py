import common, os

class test_status(common.basetest):
    def test_empty(self):
        self.assertEquals(self.client.status(), [])

    def test_one_of_each(self):
        self.append('.hgignore', 'ignored')
        self.append('ignored', 'a')
        self.append('clean', 'a')
        self.append('modified', 'a')
        self.append('removed', 'a')
        self.append('missing', 'a')
        self.client.commit('first', addremove=True)
        self.append('modified', 'a')
        self.append('added', 'a')
        self.client.add(['added'])
        os.remove('missing')
        self.client.remove(['removed'])
        self.append('untracked')

        l = [('M', 'modified'),
             ('A', 'added'),
             ('R', 'removed'),
             ('C', '.hgignore'),
             ('C', 'clean'),
             ('!', 'missing'),
             ('?', 'untracked'),
             ('I', 'ignored')]

        st = self.client.status(all=True)

        for i in l:
            self.assertTrue(i in st)

    def test_copy(self):
        self.append('source', 'a')
        self.client.commit('first', addremove=True)
        self.client.copy('source', 'dest')
        l = [('A', 'dest'), (' ', 'source')]
        self.assertEquals(self.client.status(copies=True), l)

    def test_copy_origin_space(self):
        self.append('s ource', 'a')
        self.client.commit('first', addremove=True)
        self.client.copy('s ource', 'dest')
        l = [('A', 'dest'), (' ', 's ource')]
        self.assertEquals(self.client.status(copies=True), l)
