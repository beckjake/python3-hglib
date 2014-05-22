import common, hglib, datetime
from hglib.error import CommandError

class test_obsolete_reference(common.basetest):
    '''make sure obsolete changesets are disabled'''
    def test_debugobsolete_failure(self):
        f = open('gna1','w')
        f.write('g')
        f.close()
        self.client.add('gna1')
        cs = self.client.commit('gna1')[1] #get id
        with self.assertRaises(CommandError):
            self.client.rawcommand(['debugobsolete', cs])


class test_obsolete(common.basetest):
    '''test a few client methods with obsolete changesets enabled'''
    def setUp(self):
        #create an extension which only activates obsolete
        super(test_obsolete, self).setUp()
        self.append('.hg/obs.py','''import mercurial.obsolete\nmercurial.obsolete._enabled = True''')
        self.append('.hg/hgrc','\n[extensions]\nobs=.hg/obs.py')

    def test_debugobsolete_success(self):
        self.append('gna1','ga')
        self.client.add('gna1')
        cs = self.client.commit('gna1')[1] #get id
        self.client.rawcommand(['debugobsolete', cs])

    def test_obsolete_in(self):
        self.append('gna1','ga')
        self.client.add('gna1')
        cs0 = self.client.commit('gna1')[1] #get id
        self.append('gna2','gaaa')
        self.client.add('gna2')
        cs1 = self.client.commit('gna2')[1] #get id
        self.client.rawcommand(['debugobsolete', cs1])
        self.client.update(cs0)
        self.assertFalse(cs1 in self.client)
        self.assertTrue(cs0 in self.client)
        self.client.hidden = True
        self.assertTrue(cs1 in self.client)

