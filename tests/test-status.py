import common, os

class test_status(common.basetest):
    def test_empty(self):
        d = dict((c, []) for c in 'MARC!?I')
        self.assertEquals(self.client.status(), d)

    def test_one_of_each(self):
        self.append('.hgignore', 'ignored')
        self.append('ignored', 'a')
        self.append('clean', 'a')
        self.append('modified', 'a')
        self.append('removed', 'a')
        self.append('missing', 'a')
        rev0 = self.client.commit('first', addremove=True)
        self.append('modified', 'a')
        self.append('added', 'a')
        self.client.add(['added'])
        os.remove('missing')
        self.client.remove(['removed'])
        self.append('untracked')

        d = {'M' : ['modified'],
             'A' : ['added'],
             'R' : ['removed'],
             'C' : ['.hgignore', 'clean'],
             '!' : ['missing'],
             '?' : ['untracked'],
             'I' : ['ignored']}

        self.assertEquals(self.client.status(all=True), d)
