import common, hglib, os, stat

class test_manifest(common.basetest):
    def test_basic(self):
        self.append('a', 'a')
        files = ['a']
        manifest = [('047b75c6d7a3ef6a2243bd0e99f94f6ea6683597', '644', False,
                     False, 'a')]

        if os.name == 'posix':
            self.append('b', 'b')
            os.chmod('b', os.stat('b')[0] | stat.S_IEXEC)
            os.symlink('b', 'c')

            files.extend(['b', 'c'])
            manifest.extend([('62452855512f5b81522aa3895892760bb8da9f3f', '755',
                              True, False, 'b'),
                             ('62452855512f5b81522aa3895892760bb8da9f3f', '644',
                              False, True, 'c')])

        self.client.commit('first', addremove=True)

        self.assertEquals(list(self.client.manifest(all=True)), files)

        self.assertEquals(list(self.client.manifest()), manifest)
