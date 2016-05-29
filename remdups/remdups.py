#! /usr/bin/env python
# -*- coding: utf-8 -*

# Homepage: https://github.org/rpuntaie/remdups
# License: See LICENSE file

# Authors:
# Roland Puntaier

# Changes:
# 2013-10-07: Version 1.0
# 2013-10-31: Version 1.1 (documentation changes/corrections)
# 2016-05-29: Version 1.2 (fails to install -> fix)

r'''
Create shell script to remove duplicates, for further inspection.

Use like this:

1. create file hash list:

     $remdups --hash > hashes.txt

   or

     $find . -not -type d -exec sha256sum {} \; >> hashes.txt

2. make a script with remove commands

   $remdups hashes.txt rmfiles.sh

3. inspect the script and go back to 2., if necessary, else 4.

4. execute script

   $./rmfiles.sh

'''

import sys
import os
import os.path
try:
    from itertools import zip_longest  # pragma: no cover
except ImportError:  # pragma: no cover
    from itertools import izip_longest as zip_longest  # pragma: no cover
import filecmp
import hashlib
import re

__all__ = ['sources', 'hash_file', 'walkhash',
           'same_tail', 'Hashlist', 'remdups']

__version__ = '1.2' #this is also in setup.py
__appname__ = "Remove Duplicate Files"
__author__  = "Roland Puntaier <roland.puntaier@gmail.com>"
__license__ = "The MIT License (MIT)"

PY3 = sys.version_info[0] == 3

sources = {'name': 'Create file hash using only file name.',
           'namedate': 'Create file hash using only '
                       'file name and modification date.',
           'exif': 'Create file hash using only image EXIF data, '
                   'thus recognizing equality for different compressions',
           'content': 'Create file hash using whole file content.',
           'block': 'Create file hash using a starting block.'}

encoding = sys.getfilesystemencoding()

def encode(code):
    'return bytes for python 2 and 3'
    if PY3:
        return bytes(code, encoding) # pragma: no cover
    else:  # pragma: no cover
        return code  # pragma: no cover

def hash_file(filename
        , source = 'content'
        , hasher = hashlib.sha256
        ):
    '''hash a file, no size limit
    '''
    blocksize = filecmp.BUFSIZE
    _hasher = hasher()
    if source in {'content', 'block'}:
        with open(filename, 'rb') as _file:
            buf = _file.read(blocksize)
            while len(buf) > 0:
                _hasher.update(buf)
                if source == 'block':
                    break
                buf = _file.read(blocksize)
    elif source == 'name':
        _hasher.update(encode(os.path.split(filename)[1]))
    elif source == 'namedate':
        _hasher.update(encode(os.path.split(filename)[1] +
            str(os.path.getmtime(filename))))
    elif source == 'exif':
        try:
            from PIL import Image
            img = Image.open(filename)
            exif_data = img._getexif()
            _hasher.update(encode(os.path.split(filename)[1] + str(exif_data)))
        except:
            return hash_file(filename, 'content', hasher)
    return _hasher.hexdigest()


def walkhash(
          hashfile=hash_file
        , startdir='.'
        , exclude_dirs=[]
        ):
    ''' generator for hashes (hash-path tuples) for directory tree
    >>> '[(' in str(list(walkhash(exclude_dirs=['__pycache__'])))
    True

    '''
    for root, dirs, files in os.walk(startdir):
        for name in files:
            path = os.path.join(root, name)
            yield (hashfile(path), path)
        for exclude in exclude_dirs:
            if exclude in dirs:
                dirs.remove(exclude)


def same_tail(paths):
    '''return common tail of paths if any
    >>> paths = ['b/a', 'c/a', 'u/v/a']
    >>> same_tail(paths)
    'a'
    >>> paths = ['b/x', 'c/x', 'u/v/y']
    >>> same_tail(paths)
    ''

    '''
    spathreversed = [list(reversed(p.split(os.sep))) for p in paths]
    allsame = lambda e: all([e[0] == x for x in e])
    _sametail = []
    for pathentry in zip_longest(*spathreversed):
        if allsame(pathentry):
            _sametail.append(pathentry[0])
        else:
            break
    savejoin = lambda *x: os.path.join(*x) if x else ''
    return savejoin(*reversed(_sametail))


make_hash_path = lambda h, p: '{}  {}'.format(h, p)


class Hashlist(object):

    '''represents the file hash list'''

    def __init__(self, hashpaths):
        self.path_hash = {p: h for h, p in hashpaths}
        self.hash_paths = {}
        for path, _hash in self.path_hash.items():
            self.hash_paths.setdefault(_hash, []).append(path)
        # for these call find_dups first
        self.with_same_tail = None
        self.no_same_tail = None

    def hashpaths(self):
        '''format as given by system tools like sha256sum'''
        return [make_hash_path(h, p) for p, h in self.path_hash.items()]

    def where_name(self, tail):
        '''return path groups without this tail
        self = hashlist
        '''
        return [paths for t, paths in self.with_same_tail if t.endswith(tail)]

    def where_file(self, filepath):
        '''return path groups without this tail
        self = hashlist
        filepath = 'k/h'
        '''
        try:
            _hash = self.path_hash[filepath]
        except KeyError:
            _hash = [h for p, h in self.path_hash.items() if filepath in p]
            if not _hash or len(_hash) > 1:
                raise ValueError('Path does not uniquely define a file')
            _hash = _hash[0]
        return self.hash_paths[_hash]

    def find_dups(self
            , only_same_name = False
            , safe = False
            ):
        '''returns groups of same files tuple (no same name, with same name)
        '''
        dups = [
            paths for h, paths in self.hash_paths.items() if len(paths) > 1]

        def safe_cmp(tail_files):
            '''form groups based on bytewise comparison'''
            for tail, files in tail_files:
                cnt = 0
                while len(files) > 1:
                    this, new = [], []
                    first = files[0]
                    this.append(first)
                    for other in files[1:]:
                        try:
                            same = filecmp.cmp(first, other, False)
                        except (OSError, IOError): # pragma no cover
                            same = True # pragma no cover
                        if same:
                            this.append(other)
                        else:
                            new.append(other)
                    if len(this) > 1:
                        yield (('group {}: '.format(cnt) if cnt else '') + tail,
                                this)
                        cnt += 1
                    files = new

        tail_paths = [(same_tail(paths), paths) for paths in dups]
        self.no_same_tail = None
        if not only_same_name:
            self.no_same_tail = [(tail, paths)
                                 for tail, paths in tail_paths if tail == '']
            if safe:
                self.no_same_tail = list(safe_cmp(self.no_same_tail))
        self.with_same_tail = [(tail, paths)
                               for tail, paths in tail_paths if tail != '']
        if safe:
            self.with_same_tail = list(safe_cmp(self.with_same_tail))
        return (self.no_same_tail, self.with_same_tail)

def remdups(
      infile = None
    , outfile = None
    , remove_command = 'rm -f'
    , remove_dir_command = 'rm -rf'
    , only_same_name = False
    , safe = False
    , keep_in = []
    , keep_out = []
    , comment_out = []
    , html_files_suffix = '_files'
    , method = 'sha256'
    , source = 'content'
    , hashonly = False
    , exclude_dir = []
    , where_name = None
    , where_file = None
    ):
    '''makes the program's functionality available to from within python'''

    hasher = eval('hashlib.' + method)
    _hash_file = lambda fn: hash_file(fn, source, hasher)

    if hashonly and infile:
        _hashpath = make_hash_path(_hash_file(infile.name), infile.name)
        if outfile != None:
            outfile.writelines(_hashpath)
            outfile.write('\n')
            return outfile
        else:
            return _hashpath

    def html_files(filename):
        '''check whether filename is a saved html file'''
        res = False
        if html_files_suffix + os.sep in filename:
            filename = filename.split(html_files_suffix)[0]
            res = (os.path.exists(filename + '.html')
                   or os.path.exists(filename + '.htm'))
        return res

    comment_outs = [html_files]
    for cmnt in comment_out:
        comment_outs.append(lambda x, c=cmnt: c in x)

    keepers = []
    for keepin in keep_in:
        keepers.append(lambda values: filter(
            lambda x, k=keepin: k in x, values))
    for keepout in keep_out:
        keepers.append(lambda values: filter(
            lambda x, k=keepout: k not in x, values))

    def rmcmd(filepath):
        '''yield one remove command'''
        yield remove_command + ' "' + filepath + '"'
        filename, ext = os.path.splitext(filepath)
        if '.htm' in ext:
            htmlfiles = filename + html_files_suffix
            if os.path.exists(htmlfiles):
                yield remove_dir_command + ' "' + htmlfiles + '"'

    def gen_rem(tail_same):
        '''yield all remove commands'''
        lenk = lambda x: len(x)
        equal = lambda x: x
        tokeep = keepers + [equal]
        for tail, same in tail_same:
            yield ''
            yield '#:#' + tail + '{{{'
            # take the shortest path in the smallest set
            keep = sorted(filter(equal,
                [sorted(kp(same), key=lenk) for kp in tokeep]), key=lenk)[0][0]
            for filename in sorted(same):
                comment = ''
                if any([cmnt(filename) for cmnt in comment_outs]):
                    comment = '#c#'
                elif filename == keep:
                    comment = '#'
                for command in rmcmd(filename):
                    yield comment + command
            yield '#:#}}}'

    if infile:
        hashlist = Hashlist(re.split(r'\s+', e.strip(), maxsplit=1)
                            for e in infile.read(-1).splitlines())
    else:
        hashpaths = walkhash(hashfile=_hash_file, exclude_dirs=exclude_dir)
        hashlist = Hashlist(hashpaths)

    if hashonly:
        rems = hashlist.hashpaths()
    else:
        grps_no, grps_with = hashlist.find_dups(
            only_same_name=only_same_name, safe=safe)

        if where_name:
            rems = []
            wheregroups = hashlist.where_name(where_name)
            for wheregroup in wheregroups:
                for where in wheregroup:
                    rems.append(where)
                rems.append('')
        elif where_file:
            rems = hashlist.where_file(where_file)
        else:  # script
            rems = []
            if grps_no or grps_with:
                rems.append('### vim: set fdm=marker')
            if grps_no:
                rems.append('')
                rems.append('### No Same Tail {{{')
                for line in gen_rem(grps_no):
                    rems.append(line)
                rems.append('### }}}')
            if grps_with:
                rems.append('')
                rems.append('### With Same Tail {{{')
                for line in gen_rem(grps_with):
                    rems.append(line)
                rems.append('### }}}')

    if outfile != None:
        script = '\n'.join(rems)
        outfile.write(script)
        return outfile
    else:
        return rems


def args():
    '''parses the arguments and returns a dictionary of them'''
    import argparse

    parser = argparse.ArgumentParser(description = __doc__,
            formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    # script creation
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'))
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout)
    parser.add_argument('-n', '--only-same-name', action='store_true',
        help='Only consider files with same name')
    parser.add_argument('-s', '--safe', action='store_true',
        help='Do not trust filename+hash, '
             'but do an additional bytewise compare.')
    parser.add_argument(
        '-r', '--remove-command', action='store', default='rm -f',
        help='The shell command to remove a file.')
    parser.add_argument(
        '-d', '--remove-dir-command', action='store', default='rm -rf',
        help='The shell command to remove a directory.')
    parser.add_argument(
        '-x', '--html-files-suffix', action='store', default='_files',
        help='When saving an html '
        'the files get into a subfolder formed with a suffix to the html file.'
        'User = for suffixes starting with a hyphen, like: -x="-Dateien".')
    parser.add_argument('-i', '--keep-in', action='append', default=[],
        help='Add substring to make other files of the duplicates be removed.')
    parser.add_argument('-o', '--keep-out', action='append', default=[],
        help='Add substring to make this files of the duplicates be removed.')
    parser.add_argument('-c', '--comment-out', action='append', default=[],
        help='Add substring to make the remove command '
        'for the file containing it be commented out.')
    parser.add_argument('-e', '--exclude-dir', action='append', default=[],
        help='Exclude such dir names when walking the directory tree.')
    parser.add_argument('-m', '--method', action='store', default='sha256',
        help='Any of md5, sha1, sha224, sha256, sha384, sha512.')
    # hash creation
    parser.add_argument('--hash', dest='hashonly', action='store_true',
        help='Hash only. With no input file it produces file hashes '
        'of the current directory tree. With input file it produces '
        'a hash of that file and can replace a system tool like sha256sum.')
    group = parser.add_mutually_exclusive_group()
    for k, sourcetype in sources.items():
        group.add_argument('--' + k, dest='source', 
                default = True if k=='content' else False,
                action='store_const', const=k, help=sourcetype)

    # query
    parser.add_argument('-w', '--where-name', action='store',
        help='All places for this name, grouped by same hash.')
    parser.add_argument('-W', '--where-file', action='store',
        help='All places for the hash of this file.')

    argdict = vars(parser.parse_args())  # exception when using py.test

    if not argdict['source']:  # pragma no cover
        argdict['source'] = 'content'  # pragma: no cover

    return argdict  # pragma: no cover

def main():
    remdups(**args())  # pragma: no cover

if __name__ == '__main__':
    main()

