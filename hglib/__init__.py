from client import hgclient

HGPATH = 'hg'

def open(path=None, encoding=None, configs=None):
    ''' starts a cmdserver for the given path (or for a repository found in the
    cwd). HGENCODING is set to the given encoding. configs is a list of key, value,
    similar to those passed to hg --config. '''
    return hgclient(path, encoding, configs)
