import subprocess, os, struct, cStringIO, collections
import hglib, error, util, templates

from util import cmdbuilder

class hgclient(object):
    inputfmt = '>I'
    outputfmt = '>cI'
    outputfmtsize = struct.calcsize(outputfmt)
    retfmt = '>i'

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

    def rawcommand(self, args, eh=None, prompt=None, input=None):
        """
        args is the cmdline (usually built using util.cmdbuilder)

        eh is an error handler that is passed the return code, stdout and stderr
        If no eh is given, we raise a CommandError if ret != 0

        prompt is used to reply to prompts by the server
        It receives the max number of bytes to return and the contents of stdout
        received so far

        input is used to reply to bulk data requests by the server
        It receives the max number of bytes to return
        """

        out, err = cStringIO.StringIO(), cStringIO.StringIO()
        outchannels = {'o' : out.write, 'e' : err.write}

        inchannels = {}
        if prompt is not None:
            def func(size):
                reply = prompt(size, out.getvalue())
                return str(reply)
            inchannels['L'] = func
        if input is not None:
            inchannels['I'] = input

        ret = self.runcommand(args, inchannels, outchannels)
        out, err = out.getvalue(), err.getvalue()

        if ret:
            if eh is None:
                raise error.CommandError(args, ret, out, err)
            else:
                return eh(ret, out, err)
        return out

    def close(self):
        self.server.stdin.close()
        self.server.wait()
        ret = self.server.returncode
        self.server = None
        return ret

    def branch(self, name=None, clean=False, force=False):
        if name and clean:
            raise ValueError('cannot use both name and clean')

        args = cmdbuilder('branch', name, f=force, C=clean)
        out = self.rawcommand(args).rstrip()

        if name:
            return name
        elif not clean:
            return out
        else:
            # len('reset working directory to branch ') == 34
            return out[34:]

    def branches(self, active=False, closed=False):
        args = cmdbuilder('branches', a=active, c=closed)
        out = self.rawcommand(args)

        branches = []
        for line in out.rstrip().splitlines():
            name, line = line.split(' ', 1)
            rev, node = line.split(':')
            node = node.split()[0] # get rid of ' (inactive)'
            branches.append((name, int(rev), node))
        return branches

    def cat(self, files, rev=None, output=None):
        args = cmdbuilder('cat', *files, r=rev, o=output)
        out = self.rawcommand(args)

        if not output:
            return out

    def clone(self, source='.', dest=None, branch=None, updaterev=None,
              revrange=None):
        args = cmdbuilder('clone', source, dest, b=branch, u=updaterev, r=revrange)
        self.rawcommand(args)

    def commit(self, message, addremove=False):
        # --debug will print the committed cset
        args = cmdbuilder('commit', debug=True, m=message, A=addremove)

        out = self.rawcommand(args)
        rev, node = out.splitlines()[-1].rsplit(':')
        return int(rev.split()[-1]), node

    def config(self, refresh=False):
        if not self._config or refresh:
            self._config.clear()

            out = self.rawcommand(['showconfig'])

            for entry in cStringIO.StringIO(out):
                k, v = entry.rstrip().split('=', 1)
                section, name = k.split('.', 1)
                self._config.setdefault(section, {})[name] = v

        return self._config

    @property
    def encoding(self):
        """ get the servers encoding """
        if not 'getencoding' in self.capabilities:
            raise CapabilityError('getencoding')

        if not self._encoding:
            self.server.stdin.write('getencoding\n')
            self._encoding = self._readfromchannel('r')

        return self._encoding

    def import_(self, patches, strip=None, force=False, nocommit=False,
                bypass=False, exact=False, importbranch=False, message=None,
                date=None, user=None, similarity=None):
        """
        patches can be a list of file names with patches to apply
        or a file-like object that contains a patch (needs read and readline)
        """
        if hasattr(patches, 'read') and hasattr(patches, 'readline'):
            patch = patches

            def readline(size, output):
                return patch.readline(size)

            stdin = True
            patches = ()
            prompt = readline
            input = patch.read
        else:
            stdin = False
            prompt = None
            input = None

        args = cmdbuilder('import', *patches, strip=strip, force=force,
                          nocommit=nocommit, bypass=bypass, exact=exact,
                          importbranch=importbranch, message=message,
                          date=date, user=user, similarity=similarity, _=stdin)

        self.rawcommand(args, prompt=prompt, input=input)

    def incoming(self, revrange=None, path=None):
        args = cmdbuilder('incoming',
                          path,
                          template=templates.changeset, rev=revrange)

        def eh(ret, out, err):
            if ret != 1:
                raise error.CommandError(args, ret, out, err)

        out = self.rawcommand(args, eh=eh)
        if not out:
            return []

        out = util.eatlines(out, 2).split('\0')[:-1]
        return self._parserevs(out)

    def log(self, revrange=None):
        args = cmdbuilder('log', template=templates.changeset, rev=revrange)

        out = self.rawcommand(args)
        out = out.split('\0')[:-1]

        return self._parserevs(out)

    def outgoing(self, revrange=None, path=None):
        args = cmdbuilder('outgoing',
                          path, template=templates.changeset, rev=revrange)

        def eh(ret, out, err):
            if ret != 1:
                raise error.CommandError(args, ret, out, err)

        out = self.rawcommand(args, eh=eh)
        if not out:
            return []

        out = util.eatlines(out, 2).split('\0')[:-1]
        return self._parserevs(out)

    def paths(self, name=None):
        if not name:
            out = self.rawcommand(['paths'])
            if not out:
                return {}

            return dict([s.split(' = ') for s in out.rstrip().split('\n')])
        else:
            args = cmdbuilder('paths', name)
            out = self.rawcommand(args)
            return out.rstrip()

    def root(self):
        return self.rawcommand(['root']).rstrip()

    def status(self):
        out = self.rawcommand(['status', '-0'])

        d = dict((c, []) for c in 'MARC!?I')

        for entry in out.split('\0'):
            if entry:
                t, f = entry.split(' ', 1)
                d[t].append(f)

        return d

    def tip(self):
        args = cmdbuilder('tip', template=templates.changeset)
        out = self.rawcommand(args)
        out = out.split('\0')

        return self._parserevs(out)[0]

