import subprocess, os, struct, cStringIO, collections
import hglib, error, util

from util import cmdbuilder

class hgclient(object):
    inputfmt = '>I'
    outputfmt = '>cI'
    outputfmtsize = struct.calcsize(outputfmt)
    retfmt = '>i'

    # XXX fix this hack
    _stylesdir = os.path.join(os.path.dirname(__file__), 'styles')
    revstyle = os.path.join(_stylesdir, 'rev.style')

    revision = collections.namedtuple('revision', 'rev, node, tags, '
                                                  'branch, author, desc')

    def __init__(self, path, encoding, configs):
        args = [hglib.HGPATH, 'serve', '--cmdserver', 'pipe']
        if path:
            args += ['-R', path]
        if configs:
            args += ['--config'] + configs
        env = dict(os.environ)
        if encoding:
            env['HGENCODING'] = encoding

        self.server = subprocess.Popen(args, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, env=env)

        self._readhello()
        self._config = {}

    def _readhello(self):
        """ read the hello message the server sends when started """
        ch, msg = self._readchannel()
        assert ch == 'o'

        msg = msg.split('\n')

        self.capabilities = msg[0][len('capabilities: '):]
        if not self.capabilities:
            raise error.ResponseError("bad hello message: expected 'capabilities: '"
                                      ", got %r" % msg[0])

        self.capabilities = set(self.capabilities.split())

        # at the very least the server should be able to run commands
        assert 'runcommand' in self.capabilities

        self._encoding = msg[1][len('encoding: '):]
        if not self._encoding:
            raise error.ResponseError("bad hello message: expected 'encoding: '"
                                      ", got %r" % msg[1])

    def _readchannel(self):
        data = self.server.stdout.read(hgclient.outputfmtsize)
        if not data:
            raise error.ServerError()
        channel, length = struct.unpack(hgclient.outputfmt, data)
        if channel in 'IL':
            return channel, length
        else:
            return channel, self.server.stdout.read(length)

    def _parserevs(self, splitted):
        ''' splitted is a list of fields according to our rev.style, where each 6
        fields compose one revision. '''
        return [self.revision._make(rev) for rev in util.grouper(6, splitted)]

    def _eatlines(self, s, n):
        idx = 0
        for i in xrange(n):
            idx = s.find('\n', idx) + 1

        return s[idx:]

    def runcommand(self, args, inchannels, outchannels):
        def writeblock(data):
            self.server.stdin.write(struct.pack(self.inputfmt, len(data)))
            self.server.stdin.write(data)
            self.server.stdin.flush()

        if not self.server:
            raise ValueError("server not connected")

        self.server.stdin.write('runcommand\n')
        writeblock('\0'.join(args))

        while True:
            channel, data = self._readchannel()

            # input channels
            if channel in inchannels:
                writeblock(inchannels[channel](data))
            # output channels
            elif channel in outchannels:
                outchannels[channel](data)
            # result channel, command finished
            elif channel == 'r':
                return struct.unpack(hgclient.retfmt, data)[0]
            # a channel that we don't know and can't ignore
            elif channel.isupper():
                raise error.ResponseError("unexpected data on required channel '%s'"
                                          % channel)
            # optional channel
            else:
                pass

    def outputruncommand(self, args, inchannels = {}, raiseonerror=True):
        ''' run the command specified by args, returning (ret, output, error) '''
        out, err = cStringIO.StringIO(), cStringIO.StringIO()
        outchannels = {'o' : out.write, 'e' : err.write}
        ret = self.runcommand(args, inchannels, outchannels)
        if ret and raiseonerror:
            raise error.CommandError(args, ret, out.getvalue(), err.getvalue())
        return ret, out.getvalue(), err.getvalue()

    def close(self):
        self.server.stdin.close()
        self.server.wait()
        ret = self.server.returncode
        self.server = None
        return ret

    @property
    def encoding(self):
        """ get the servers encoding """
        if not 'getencoding' in self.capabilities:
            raise CapabilityError('getencoding')

        if not self._encoding:
            self.server.stdin.write('getencoding\n')
            self._encoding = self._readfromchannel('r')

        return self._encoding

    def config(self, refresh=False):
        if not self._config or refresh:
            self._config.clear()

            ret, out, err = self.outputruncommand(['showconfig'])
            if ret:
                raise error.CommandError(['showconfig'], ret, out, err)

            for entry in cStringIO.StringIO(out):
                k, v = entry.rstrip().split('=', 1)
                section, name = k.split('.', 1)
                self._config.setdefault(section, {})[name] = v

        return self._config

    def status(self):
        ret, out = self.outputruncommand(['status', '-0'])

        d = dict((c, []) for c in 'MARC!?I')

        for entry in out.split('\0'):
            if entry:
                t, f = entry.split(' ', 1)
                d[t].append(f)

        return d

    def log(self, revrange=None):
        args = cmdbuilder('log', style=hgclient.revstyle, rev=revrange)

        out = self.outputruncommand(args)[1]
        out = out.split('\0')[:-1]

        return self._parserevs(out)

    def incoming(self, revrange=None, path=None):
        args = cmdbuilder('incoming',
                          path,
                          style=hgclient.revstyle, rev=revrange)

        ret, out, err = self.outputruncommand(args, raiseonerror=False)
        if not ret:
            out = self._eatlines(out, 2).split('\0')[:-1]
            return self._parserevs(out)
        elif ret == 1:
            return []
        else:
            raise error.CommandError(args, ret, out, err)

    def outgoing(self, revrange=None, path=None):
        args = cmdbuilder('outgoing',
                          path, style=hgclient.revstyle, rev=revrange)

        ret, out, err = self.outputruncommand(args, raiseonerror=False)
        if not ret:
            out = self._eatlines(out, 2).split('\0')[:-1]
            return self._parserevs(out)
        elif ret == 1:
            return []
        else:
            raise error.CommandError(args, ret, out, err)

    def commit(self, message, addremove=False):
        args = cmdbuilder('commit', m=message, A=addremove)

        self.outputruncommand(args)

        # hope the tip hasn't changed since we committed
        return self.tip()

    def import_(self, patch):
        if isinstance(patch, str):
            fp = open(patch)
        else:
            assert hasattr(patch, 'read')
            assert hasattr(patch, 'readline')

            fp = patch

        try:
            inchannels = {'I' : fp.read, 'L' : fp.readline}
            self.outputruncommand(cmdbuilder('import', _=True), inchannels)
        finally:
            if fp != patch:
                fp.close()

    def root(self):
        return self.outputruncommand(['root'])[1].rstrip()

    def clone(self, source='.', dest=None, branch=None, updaterev=None,
              revrange=None):
        args = cmdbuilder('clone', source, dest, b=branch, u=updaterev, r=revrange)
        self.outputruncommand(args)

    def tip(self):
        args = cmdbuilder('tip', style=hgclient.revstyle)
        out = self.outputruncommand(args)[1]
        out = out.split('\0')

        return self._parserevs(out)[0]

    def branch(self, name=None):
        if not name:
            return self.outputruncommand(['branch'])[1].rstrip()

    def branches(self):
        out = self.outputruncommand(['branches'])[1]
        branches = {}
        for line in out.rstrip().split('\n'):
            branch, revnode = line.split()
            branches[branch] = self.log(revrange=[revnode.split(':')[0]])[0]

        return branches

    def paths(self, name=None):
        if not name:
            out = self.outputruncommand(['paths'])[1]
            if not out:
                return {}

            return dict([s.split(' = ') for s in out.rstrip().split('\n')])
        else:
            args = cmdbuilder('paths', name)
            ret, out, err = self.outputruncommand(args, raiseonerror=False)
            if ret:
                raise error.CommandError(args, ret, out, err)
            return out.rstrip()

    def cat(self, files, rev=None, output=None):
        args = cmdbuilder('cat', *files, r=rev, o=output)
        ret, out, err = self.outputruncommand(args)

        if not output:
            return out
