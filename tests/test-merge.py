import common, hglib

class test_merge(common.basetest):
    def setUp(self):
        common.basetest.setUp(self)

        self.append('a', 'a')
        rev, self.node0 = self.client.commit('first', addremove=True)

        self.append('a', 'a')
        rev, self.node1 = self.client.commit('change')

    def test_basic(self):
        self.client.update(self.node0)
        self.append('b', 'a')
        rev, node2 = self.client.commit('new file', addremove=True)
        self.client.merge(self.node1)
        rev, node = self.client.commit('merge')
        diff = """diff -r %s -r %s a
--- a/a
+++ b/a
@@ -1,1 +1,1 @@
-a
\ No newline at end of file
+aa
\ No newline at end of file
""" % (node2[:12], node[:12])

        self.assertEquals(diff, self.client.diff(change=node, nodates=True))

    def test_merge_prompt_abort(self):
        self.client.update(self.node0)
        self.client.remove('a')
        self.client.commit('remove')

        self.assertRaises(hglib.error.CommandError, self.client.merge)

    def test_merge_prompt_noninteractive(self):
        self.client.update(self.node0)
        self.client.remove('a')
        rev, node = self.client.commit('remove')

        self.client.merge(cb=hglib.merge.handlers.noninteractive)

        diff = """diff -r %s a
--- /dev/null
+++ b/a
@@ -0,0 +1,1 @@
+aa
\ No newline at end of file
""" % node[:12]
        self.assertEquals(diff, self.client.diff(nodates=True))

    def test_merge_prompt_cb(self):
        self.client.update(self.node0)
        self.client.remove('a')
        rev, node = self.client.commit('remove')

        def cb(output):
            return 'c'

        self.client.merge(cb=cb)

        diff = """diff -r %s a
--- /dev/null
+++ b/a
@@ -0,0 +1,1 @@
+aa
\ No newline at end of file
""" % node[:12]
        self.assertEquals(diff, self.client.diff(nodates=True))
