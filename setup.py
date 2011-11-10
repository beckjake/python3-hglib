import os, time
from distutils.core import setup

# query Mercurial for version number
version = 'unknown'
if os.path.isdir('.hg'):
    cmd = "hg id -i -t"
    l = os.popen(cmd).read().split()
    while len(l) > 1 and l[-1][0].isalpha(): # remove non-numbered tags
        l.pop()
    if len(l) > 1: # tag found
        version = l[-1]
        if l[0].endswith('+'): # propagate the dirty status to the tag
            version += '+'
    elif len(l) == 1: # no tag found
        cmd = 'hg parents --template "{latesttag}+{latesttagdistance}-"'
        version = os.popen(cmd).read() + l[0]
    if version.endswith('+'):
        version += time.strftime('%Y%m%d')
elif os.path.exists('.hg_archival.txt'):
    kw = dict([[t.strip() for t in l.split(':', 1)]
               for l in open('.hg_archival.txt')])
    if 'tag' in kw:
        version =  kw['tag']
    elif 'latesttag' in kw:
        version = '%(latesttag)s+%(latesttagdistance)s-%(node).12s' % kw
    else:
        version = kw.get('node', '')[:12]

setup(
    name='python-hglib',
    version=version,
    author='Idan Kamara',
    author_email='idankk86@gmail.com',
    url='http://selenic.com/repo/python-hglib',
    description='Mercurial Python library',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    license='MIT',
    packages=['hglib'])
