import common, cStringIO
import hglib

class test_import(common.basetest):
    def test_basic(self):
        patch = """
# HG changeset patch
# User test
# Date 0 0
# Node ID c103a3dec114d882c98382d684d8af798d09d857
# Parent  0000000000000000000000000000000000000000
1

diff -r 000000000000 -r c103a3dec114 a
--- /dev/null	Thu Jan 01 00:00:00 1970 +0000
+++ b/a	Thu Jan 01 00:00:00 1970 +0000
@@ -0,0 +1,1 @@
+1
"""
        self.client.import_(cStringIO.StringIO(patch))
        self.assertEquals(self.client.cat(['a']), '1\n')