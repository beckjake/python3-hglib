import common
import hglib

class test_summary(common.basetest):
    def test_empty(self):
        d = {'parent' : [(-1, '000000000000', 'tip', None)],
             'branch' : 'default',
             'commit' : True,
             'update' : 0}

        self.assertEquals(self.client.summary(), d)

    def test_basic(self):
        self.append('a', 'a')
        rev, node = self.client.commit('first', addremove=True)

        d = {'parent' : [(0, node[:12], 'tip', 'first')],
             'branch' : 'default',
             'commit' : True,
             'update' : 0}

        self.assertEquals(self.client.summary(), d)

    def test_commit_dirty(self):
        self.append('a', 'a')
        rev, node = self.client.commit('first', addremove=True)
        self.append('a', 'a')

        d = {'parent' : [(0, node[:12], 'tip', 'first')],
             'branch' : 'default',
             'commit' : False,
             'update' : 0}

        self.assertEquals(self.client.summary(), d)

    def test_update(self):
        self.append('a', 'a')
        rev, node = self.client.commit('first', addremove=True)
        self.append('a', 'a')
        self.client.commit('second')
        self.client.update(0)

        d = {'parent' : [(0, node[:12], None, 'first')],
             'branch' : 'default',
             'commit' : True,
             'update' : 1}

        self.assertEquals(self.client.summary(), d)

    def test_remote(self):
        self.append('a', 'a')
        rev, node = self.client.commit('first', addremove=True)

        self.client.clone(dest='other')
        other = hglib.open('other')

        d = {'parent' : [(0, node[:12], 'tip', 'first')],
             'branch' : 'default',
             'commit' : True,
             'update' : 0,
             'remote' : (0, 0, 0, 0)}

        self.assertEquals(other.summary(remote=True), d)

        self.append('a', 'a')
        self.client.commit('second')

        d['remote'] = (1, 0, 0, 0)
        self.assertEquals(other.summary(remote=True), d)

        self.client.bookmark('bm')
        d['remote'] = (1, 1, 0, 0)
        self.assertEquals(other.summary(remote=True), d)

        other.bookmark('bmother')
        d['remote'] = (1, 1, 0, 1)
        d['parent'] = [(0, node[:12], 'tip bmother', 'first')]
        self.assertEquals(other.summary(remote=True), d)

        self.append('other/a', 'a')
        rev, node = other.commit('second in other')

        d['remote'] = (1, 1, 1, 1)
        d['parent'] = [(1, node[:12], 'tip bmother', 'second in other')]

        self.assertEquals(other.summary(remote=True), d)

    def test_two_parents(self):
        self.append('a', 'a')
        rev0, node = self.client.commit('first', addremove=True)

        self.append('a', 'a')
        rev1, node1 = self.client.commit('second')

        self.client.update(rev0)
        self.append('b', 'a')
        rev2, node2 = self.client.commit('third', addremove=True)

        self.client.merge(rev1)

        d = {'parent' : [(2, node2[:12], 'tip', 'third'),
                         (1, node1[:12], None, 'second')],
             'branch' : 'default',
             'commit' : False,
             'update' : 0}

        self.assertEquals(self.client.summary(), d)
