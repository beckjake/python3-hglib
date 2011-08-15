import subprocess, os, struct, cStringIO, collections, re
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
        self._version = None

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

    def add(self, files=[], dryrun=False, subrepos=False, include=None,
            exclude=None):
        """
        Add the specified files on the next commit.
        If no files are given, add all files to the repository.

        Return whether all given files were added.
        """
        if not isinstance(files, list):
            files = [files]

        args = cmdbuilder('add', *files, n=dryrun, S=subrepos, I=include, X=exclude)

        # we could use Python 3 nonlocal here...
        warnings = [False]

        def eh(ret, out, err):
            if ret == 1:
                warnings[0] = True
            else:
                raise error.CommandError(args, ret, out, err)

        self.rawcommand(args, eh=eh)
        return not warnings[0]

    def backout(self, rev, merge=False, parent=None, tool=None, message=None,
                logfile=None, date=None, user=None):
        if message and logfile:
            raise ValueError("cannot specify both a message and a logfile")

        args = cmdbuilder('backout', r=rev, merge=merge, parent=parent, t=tool,
                          m=message, l=logfile, d=date, u=user)

        self.rawcommand(args)

    def bookmark(self, name, rev=None, force=False, delete=False, inactive=False,
                 rename=None):
        args = cmdbuilder('bookmark', name, r=rev, f=force, d=delete,
                          i=inactive, m=rename)

        self.rawcommand(args)

    def bookmarks(self):
        """
        Return the bookmarks as a list of (name, rev, node) and the
        index of the current one.

        If there isn't a current one, -1 is returned as the index
        """
        out = self.rawcommand(['bookmarks'])

        bms = []
        current = -1
        if out.rstrip() != 'no bookmarks set':
            for line in out.splitlines():
                iscurrent, line = line[0:3], line[3:]
                if '*' in iscurrent:
                    current = len(bms)
                name, line = line.split(' ', 1)
                rev, node = line.split(':')
                bms.append((name, int(rev), node))
        return bms, current

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

    def commit(self, message=None, logfile=None, addremove=False, closebranch=False,
               date=None, user=None, include=None, exclude=None):
        if message is None and logfile is None:
            raise ValueError("must provide at least a message or a logfile")
        elif message and logfile:
            raise ValueError("cannot specify both a message and a logfile")

        # --debug will print the committed cset
        args = cmdbuilder('commit', debug=True, m=message, A=addremove,
                          close_branch=closebranch, d=date, u=user, l=logfile,
                          I=include, X=exclude)

        out = self.rawcommand(args)
        rev, node = out.splitlines()[-1].rsplit(':')
        return int(rev.split()[-1]), node

    def config(self, names=[], untrusted=False, showsource=False):
        """
        Return a list of (section, key, value) config settings from all hgrc files

        When showsource is specified, return (source, section, key, value) where
        source is of the form filename:[line]
        """
        def splitline(s):
            k, value = s.rstrip().split('=', 1)
            section, key = k.split('.', 1)
            return (section, key, value)

        if not isinstance(names, list):
            names = [names]

        args = cmdbuilder('showconfig', *names, u=untrusted, debug=showsource)
        out = self.rawcommand(args)

        conf = []
        if showsource:
            out = util.skiplines(out, 'read config from: ')
            for line in out.splitlines():
                m = re.match(r"(.+?:(?:\d+:)?) (.*)", line)
                t = splitline(m.group(2))
                conf.append((m.group(1)[:-1], t[0], t[1], t[2]))
        else:
            for line in out.splitlines():
                conf.append(splitline(line))

        return conf

    @property
    def encoding(self):
        """ get the servers encoding """
        if not 'getencoding' in self.capabilities:
            raise CapabilityError('getencoding')

        if not self._encoding:
            self.server.stdin.write('getencoding\n')
            self._encoding = self._readfromchannel('r')

        return self._encoding

    def copy(self, source, dest, after=False, force=False, dryrun=False,
             include=None, exclude=None):
        if not isinstance(source, list):
            source = [source]

        source.append(dest)
        args = cmdbuilder('copy', *source, A=after, f=force, n=dryrun,
                          I=include, X=exclude)

        # we could use Python 3 nonlocal here...
        warnings = [False]

        def eh(ret, out, err):
            if ret == 1:
                warnings[0] = True
            else:
                raise error.CommandError(args, ret, out, err)

        self.rawcommand(args, eh=eh)
        return not warnings[0]

    def forget(self, files, include=None, exclude=None):
        if not isinstance(files, list):
            files = [files]

        args = cmdbuilder('forget', *files, I=include, X=exclude)

        # we could use Python 3 nonlocal here...
        warnings = [False]

        def eh(ret, out, err):
            if ret == 1:
                warnings[0] = True
            else:
                raise error.CommandError(args, ret, out, err)

        out = self.rawcommand(args, eh=eh)
        return not warnings[0]

    def diff(self, files=[], revs=[], change=None, text=False,
             git=False, nodates=False, showfunction=False, reverse=False,
             ignoreallspace=False, ignorespacechange=False, ignoreblanklines=False,
             unified=None, stat=False, subrepos=False, include=None, exclude=None):
            if change and revs:
                raise ValueError('cannot specify both change and rev')

            args = cmdbuilder('diff', *files, r=revs, c=change,
                              a=text, g=git, nodates=nodates,
                              p=showfunction, reverse=reverse,
                              w=ignoreallspace, b=ignorespacechange,
                              B=ignoreblanklines, U=unified, stat=stat,
                              S=subrepos, I=include, X=exclude)

            return self.rawcommand(args)

    def identify(self, rev=None, source=None, num=False, id=False, branch=False,
                 tags=False, bookmarks=False):
        args = cmdbuilder('identify', source, r=rev, n=num, i=id, b=branch, t=tags,
                          B=bookmarks)

        return self.rawcommand(args)

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

    def incoming(self, revrange=None, path=None, force=False, newest=False,
                 bundle=None, bookmarks=False, branch=None, limit=None,
                 nomerges=False, subrepos=False):
        """
        Return new changesets found in the specified path or the default pull
        location.

        When bookmarks=True, return a list of (name, node) of incoming bookmarks.
        """
        args = cmdbuilder('incoming',
                          path,
                          template=templates.changeset, r=revrange,
                          f=force, n=newest, bundle=bundle,
                          B=bookmarks, b=branch, l=limit, M=nomerges, S=subrepos)

        def eh(ret, out, err):
            if ret != 1:
                raise error.CommandError(args, ret, out, err)

        out = self.rawcommand(args, eh=eh)
        if not out:
            return []

        out = util.eatlines(out, 2)
        if bookmarks:
            bms = []
            for line in out.splitlines():
                bms.append(tuple(line.split()))
            return bms
        else:
            out = out.split('\0')[:-1]
            return self._parserevs(out)

    def log(self, revrange=None, files=[], follow=False, followfirst=False,
            date=None, copies=False, keyword=None, removed=False, onlymerges=False,
            user=None, branch=None, prune=None, hidden=False, limit=None,
            nomerges=False, include=None, exclude=None):
        args = cmdbuilder('log', *files, template=templates.changeset,
                          r=revrange, f=follow, follow_first=followfirst,
                          d=date, C=copies, k=keyword, removed=removed,
                          m=onlymerges, u=user, b=branch, P=prune, h=hidden,
                          l=limit, M=nomerges, I=include, X=exclude)

        out = self.rawcommand(args)
        out = out.split('\0')[:-1]

        return self._parserevs(out)

    def move(self, source, dest, after=False, force=False, dryrun=False,
             include=None, exclude=None):
        if not isinstance(source, list):
            source = [source]

        source.append(dest)
        args = cmdbuilder('move', *source, A=after, f=force, n=dryrun,
                          I=include, X=exclude)

        # we could use Python 3 nonlocal here...
        warnings = [False]

        def eh(ret, out, err):
            if ret == 1:
                warnings[0] = True
            else:
                raise error.CommandError(args, ret, out, err)

        self.rawcommand(args, eh=eh)
        return not warnings[0]

    def outgoing(self, revrange=None, path=None, force=False, newest=False,
                 bookmarks=False, branch=None, limit=None, nomerges=False,
                 subrepos=False):
        """
        Return changesets not found in the specified path or the default push
        location.

        When bookmarks=True, return a list of (name, node) of bookmarks that will
        be pushed.
        """
        args = cmdbuilder('outgoing',
                          path,
                          template=templates.changeset, r=revrange,
                          f=force, n=newest, B=bookmarks,
                          b=branch, S=subrepos)

        def eh(ret, out, err):
            if ret != 1:
                raise error.CommandError(args, ret, out, err)

        out = self.rawcommand(args, eh=eh)
        if not out:
            return []

        out = util.eatlines(out, 2)
        if bookmarks:
            bms = []
            for line in out.splitlines():
                bms.append(tuple(line.split()))
            return bms
        else:
            out = out.split('\0')[:-1]
            return self._parserevs(out)

    def parents(self, rev=None, file=None):
        args = cmdbuilder('parents', file, template=templates.changeset, r=rev)

        out = self.rawcommand(args)
        if not out:
            return

        out = out.split('\0')[:-1]

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

    def pull(self, source=None, rev=None, update=False, force=False, bookmark=None,
             branch=None, ssh=None, remotecmd=None, insecure=False, tool=None):
        args = cmdbuilder('pull', source, r=rev, u=update, f=force, B=bookmark,
                          b=branch, e=ssh, remotecmd=remotecmd, insecure=insecure,
                          t=tool)

        # we could use Python 3 nonlocal here...
        success = [True]

        def eh(ret, out, err):
            if ret == 1:
                success[0] = False
            else:
                raise error.CommandError(args, ret, out, err)

        self.rawcommand(args, eh=eh)
        return success[0]

    def push(self, dest=None, rev=None, force=False, bookmark=None, branch=None,
             newbranch=False, ssh=None, remotecmd=None, insecure=False):
        args = cmdbuilder('push', dest, r=rev, f=force, B=bookmark, b=branch,
                          new_branch=newbranch, e=ssh, remotecmd=remotecmd,
                          insecure=insecure)

        # we could use Python 3 nonlocal here...
        pushed = [True]

        def eh(ret, out, err):
            if ret == 1:
                pushed[0] = False
            else:
                raise error.CommandError(args, ret, out, err)

        self.rawcommand(args, eh=eh)
        return pushed[0]

    def remove(self, files, after=False, force=False, include=None, exclude=None):
        if not isinstance(files, list):
            files = [files]

        args = cmdbuilder('remove', *files, A=after, f=force, I=include, X=exclude)

        # we could use Python 3 nonlocal here...
        warnings = [False]

        def eh(ret, out, err):
            if ret == 1:
                warnings[0] = True
            else:
                raise error.CommandError(args, ret, out, err)

        out = self.rawcommand(args, eh=eh)
        return not warnings[0]

    def root(self):
        return self.rawcommand(['root']).rstrip()

    def status(self, rev=None, change=None, all=False, modified=False, added=False,
               removed=False, deleted=False, clean=False, unknown=False,
               ignored=False, copies=False, subrepos=False, include=None,
               exclude=None):
        """
        Return a list of (code, file path) where code can be:

                M = modified
                A = added
                R = removed
                C = clean
                ! = missing (deleted by non-hg command, but still tracked)
                ? = untracked
                I = ignored
                  = origin of the previous file listed as A (added)
        """
        if rev and change:
            raise ValueError('cannot specify both rev and change')

        args = cmdbuilder('status', rev=rev, change=change, A=all, m=modified,
                          a=added, r=removed, d=deleted, c=clean, u=unknown,
                          i=ignored, C=copies, S=subrepos, I=include, X=exclude)

        args.append('-0')

        out = self.rawcommand(args)
        l = []

        for entry in out.split('\0'):
            if entry:
                if entry[0] == ' ':
                    l.append((' ', entry[2:]))
                else:
                    l.append(tuple(entry.split(' ', 1)))

        return l

    def tag(self, names, rev=None, message=None, force=False, local=False,
            remove=False, date=None, user=None):
        if not isinstance(names, list):
            names = [names]

        args = cmdbuilder('tag', *names, r=rev, m=message, f=force, l=local,
                          remove=remove, d=date, u=user)

        self.rawcommand(args)

    def tip(self):
        args = cmdbuilder('tip', template=templates.changeset)
        out = self.rawcommand(args)
        out = out.split('\0')

        return self._parserevs(out)[0]

    def update(self, rev=None, clean=False, check=False, date=None):
        """
        Update the repository's working directory to changeset specified by rev.
        If rev isn't specified, update to the tip of the current named branch.

        Return the number of files (updated, merged, removed, unresolved)
        """
        if clean and check:
            raise ValueError('clean and check cannot both be True')

        args = cmdbuilder('update', r=rev, C=clean, c=check, d=date)

        def eh(ret, out, err):
            if ret == 1:
                return out

            raise error.CommandError(args, ret, out, err)


        out = self.rawcommand(args, eh=eh)

        # filter out 'merging ...' lines
        out = util.skiplines(out, 'merging ')

        counters = out.rstrip().split(', ')
        return tuple(int(s.split(' ', 1)[0]) for s in counters)

    @property
    def version(self):
        if self._version is None:
            v = self.rawcommand(cmdbuilder('version', q=True))
            v = list(re.match(r'.*?(\d+)\.(\d+)\.?(\d+)?(\+[0-9a-f-]+)?',
                              v).groups())

            for i in range(3):
                try:
                    v[i] = int(v[i])
                except TypeError:
                    v[i] = 0

            self._version = tuple(v)

        return self._version
