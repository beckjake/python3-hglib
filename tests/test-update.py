from . import common
from hglib import error

class test_update(common.basetest):
    def setUp(self):
        common.basetest.setUp(self)
        self.append('a', 'a')
        self.rev0, self.node0 = self.client.commit('first', addremove=True)
        self.append('a', 'a')
        self.rev1, self.node1 = self.client.commit('second')

    def test_basic(self):
        u, m, r, ur = self.client.update(self.rev0)
        self.assertEquals(u, 1)
        self.assertEquals(m, 0)
        self.assertEquals(r, 0)
        self.assertEquals(ur, 0)

    def test_unresolved(self):
        self.client.update(self.rev0)
        self.append('a', 'b')
        u, m, r, ur = self.client.update()
        self.assertEquals(u, 0)
        self.assertEquals(m, 0)
        self.assertEquals(r, 0)
        self.assertEquals(ur, 1)
        self.assertTrue(('M', 'a') in self.client.status())

    def test_merge(self):
        self.append('a', '\n\n\n\nb')
        rev2, node2 = self.client.commit('third')
        self.append('a', 'b')
        self.client.commit('fourth')
        self.client.update(rev2)
        old = open('a', 'rb').read()
        f = open('a', 'wb')
        f.write(b'a' + old)
        f.close()
        u, m, r, ur = self.client.update()
        self.assertEquals(u, 0)
        self.assertEquals(m, 1)
        self.assertEquals(r, 0)
        self.assertEquals(ur, 0)
        self.assertEquals(self.client.status(), [('M', 'a')])

    def test_tip(self):
        self.client.update(self.rev0)
        u, m, r, ur = self.client.update()
        self.assertEquals(u, 1)
        self.assertEquals(self.client.parents()[0].node, self.node1)

        self.client.update(self.rev0)
        self.append('a', 'b')
        rev2, node2 = self.client.commit('new head')
        self.client.update(self.rev0)

        self.client.update()
        self.assertEquals(self.client.parents()[0].node, node2)

    def test_check_clean(self):
        self.assertRaises(ValueError, self.client.update, clean=True, check=True)

    def test_clean(self):
        old = open('a').read()
        self.append('a', 'b')
        self.assertRaises(error.CommandError, self.client.update, check=True)

        u, m, r, ur = self.client.update(clean=True)
        self.assertEquals(u, 1)
        self.assertEquals(old, open('a').read())

    def test_basic_plain(self):
        f = open('.hg/hgrc', 'a')
        f.write('[defaults]\nupdate=-v\n')
        f.close()
        self.test_basic()

    def test_largefiles(self):
        import os
        f = open('.hg/hgrc', 'a')
        f.write('[extensions]\nlargefiles=\n')
        f.close()
        self.append('b', 'a')
        try:
            self.client.rawcommand(['add', 'b', '--large'])
        except error.CommandError:
            return

        rev2, node2 = self.client.commit('third')
        # Go back to 0
        self.client.rawcommand(['update', str(self.rev0)],
                                # Keep the 'changed' version
                               prompt=lambda s, d: b'c\n')
        u, m, r, ur = self.client.update(rev2, clean=True)
        self.assertEquals(u, 2)
        self.assertEquals(m, 0)
        self.assertEquals(r, 0)
        self.assertEquals(ur, 0)
