import common

class test_forget(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        self.client.add(['a'])
        self.assertTrue(self.client.forget('a'))

    def test_warnings(self):
        self.assertFalse(self.client.forget('a'))
        self.append('a', 'a')
        self.client.add(['a'])
        self.assertFalse(self.client.forget(['a', 'b']))
