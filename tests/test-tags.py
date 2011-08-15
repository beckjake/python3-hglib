import common
import hglib

class test_tags(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        rev, node = self.client.commit('first', addremove=True)
        self.client.tag('my tag')
        self.client.tag('local tag', rev=rev, local=True)

        # filecache that was introduced in 2.0 makes us see the local tag, for
        # now we have to reconnect
        if self.client.version < (2, 0, 0):
            self.client = hglib.open()

        tags = self.client.tags()
        self.assertEquals(tags, [('tip', 1, self.client.tip().node[:12], False),
                                 ('my tag', 0, node[:12], False),
                                 ('local tag', 0, node[:12], True)])
