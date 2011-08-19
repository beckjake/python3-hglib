import common, hglib

class test_hglib(common.basetest):
    def setUp(self):
        pass

    def test_close_fds(self):
        """
        A weird Python bug that has something to do to inherited file descriptors,
        see http://bugs.python.org/issue12786
        """
        common.basetest.setUp(self)
        client2 = hglib.open()
        self.client.close()
