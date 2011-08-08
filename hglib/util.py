import itertools

def grouper(n, iterable):
    ''' list(grouper(2, range(4))) -> [(0, 1), (2, 3)] '''
    args = [iter(iterable)] * n
    return itertools.izip(*args)

def cmdbuilder(name, *args, **kwargs):
    """
    A helper for building the command arguments

    args are the positional arguments

    kwargs are the options
    keys that are single lettered are prepended with '-', others with '--',
    underscores are replaced with dashes

    keys with False boolean values are ignored, lists add the key multiple times

    None arguments are skipped

    >>> cmdbuilder('cmd', a=True, b=False, c=None)
    ['cmd', '-a']
    >>> cmdbuilder('cmd', long=True)
    ['cmd', '--long']
    >>> cmdbuilder('cmd', str='s')
    ['cmd', '--str', 's']
    >>> cmdbuilder('cmd', d_ash=True)
    ['cmd', '--d-ash']
    >>> cmdbuilder('cmd', _=True)
    ['cmd', '-']
    >>> cmdbuilder('cmd', list=[1, 2])
    ['cmd', '--list', '1', '--list', '2']
    >>> cmdbuilder('cmd', None)
    ['cmd']
    """
    cmd = [name]
    for arg, val in kwargs.items():
        if val is None:
            continue

        arg = arg.replace('_', '-')
        if arg != '-':
            arg = '-' + arg if len(arg) == 1 else '--' + arg
        if isinstance(val, bool):
            if val:
                cmd.append(arg)
        elif isinstance(val, list):
            for v in val:
                cmd.append(arg)
                cmd.append(str(v))
        else:
            cmd.append(arg)
            cmd.append(str(val))

    for a in args:
        if a is not None:
            cmd.append(a)

    return cmd
