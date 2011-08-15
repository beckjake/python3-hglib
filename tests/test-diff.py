import common

class test_diff(common.basetest):
    def test_basic(self):
        self.append('a', 'a\n')
        self.client.add('a')
        diff1 = """diff -r 000000000000 a
--- /dev/null
+++ b/a
@@ -0,0 +1,1 @@
+a
"""
        self.assertEquals(diff1, self.client.diff(nodates=True))
        self.assertEquals(diff1, self.client.diff(['a'], nodates=True))
        rev0, node0 = self.client.commit('first')
        diff2 = """diff -r 000000000000 -r %s a
--- /dev/null
+++ b/a
@@ -0,0 +1,1 @@
+a
""" % node0[:12]
        self.assertEquals(diff2, self.client.diff(change=rev0, nodates=True))
        self.append('a', 'a\n')
        rev1, node1 = self.client.commit('second')
        diff3 = """diff -r %s a
--- a/a
+++ b/a
@@ -1,1 +1,2 @@
 a
+a
""" % node0[:12]
        self.assertEquals(diff3, self.client.diff(revs=[rev0], nodates=True))
        diff4 = """diff -r %s -r %s a
--- a/a
+++ b/a
@@ -1,1 +1,2 @@
 a
+a
""" % (node0[:12], node1[:12])
        self.assertEquals(diff4, self.client.diff(revs=[rev0, rev1], nodates=True))
