import os
from . import common
import hglib

class test_clone(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        self.client.commit('first', addremove=True)
        cloned = hglib.clone('.', 'cloned')
        self.assertRaises(ValueError, cloned.log)
        cloned.open()
        self.assertEquals(self.client.log(), cloned.log())
