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
# 2018-01-24: Version 1.3 (.remdups_c.sha256,... , options, makefile instead of script)

r'''
Create shell script to remove duplicates, for further inspection.

Use like this:

1. Create file hash list .remdups_c.sha256:

     $remdups --hash

   New files are added to .remdups. To rehash all files, first remove .remdups*.
   You can also do:

     $find . -not -type d -exec sha256sum {} \; > .remdups_c.sha256

   The first of .remdups_{c,b,d,e,n}.{sha512, sha384, sha256, sha224, sha1, md5} is used.
   Do 

      $cat > .remdups_c.sha512

   to determine the hash method in advance.

   {'c': 'content', 'b': 'block', 'd': 'date', 'e': 'exif', 'n': 'name'}

2. Make a script with (re)move commands.
   It can be repeated with different options until the script is good.

   $remdups rmfiles.sh

   If the file ends in .sh, cp is used and the file names are in linux format.
   This is usable also on Windows with MSYS, MSYS2 and CYGWIN.

   If the file ends in .bat, Windows commands are used.

3. Inspect the script and go back to 2., if necessary.
   Smaller changes to the script can also be done with the editor.

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
from itertools import product
import re

__all__ = ['sources', 'hash_file', 'walkhash',
           'same_tail', 'Hashlist', 'remdups']

__version__ = '1.3' #this is also in setup.py
__appname__ = "Remove Duplicate Files"
__author__  = "Roland Puntaier <roland.puntaier@gmail.com>"
__license__ = "The MIT License (MIT)"

sources = {
   'block': 'Create file hash using a starting block.',
   'content': 'Create file hash using whole file content.',
   'date': 'Create file hash using file name and modification date.',
   'exif': 'Create file hash using image EXIF data',
   'name': 'Create file hash using file name.',
   }

_fnencoding = sys.getfilesystemencoding()

def fnencode(code):
    'return bytes for python 2 and 3'
    if sys.version_info[0] == 3:
        return bytes(code, _fnencoding) # pragma: no cover
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
    if source in {'c', 'content', 'b', 'block'}:
        with open(filename, 'rb') as _file:
            buf = _file.read(blocksize)
            while len(buf) > 0:
                _hasher.update(buf)
                if source in {'b', 'block'}:
                    break
                buf = _file.read(blocksize)
    elif source in {'n', 'name'}:
        _hasher.update(fnencode(os.path.split(filename)[1]))
    elif source in {'d', 'date'}:
        _hasher.update(fnencode(os.path.split(filename)[1] +
            str(os.path.getmtime(filename))))
    elif source in {'e','exif'}:
        try:
            from PIL import Image
            img = Image.open(filename)
            exif_data = img._getexif()
            _hasher.update(fnencode(os.path.split(filename)[1] + str(exif_data)))
        except:
            return hash_file(filename, 'content', hasher)
    return _hasher.hexdigest()

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


make_hash_path = lambda h, p: '{}\t{}'.format(h, p)

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

    def walkhash(self
            , _hash_file=hash_file
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
                if path not in self.path_hash:
                     yield (_hash_file(path), path)
            for exclude in exclude_dirs:
                if exclude in dirs:
                    dirs.remove(exclude)

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

def convunix(fn):
    '''
    >>> fn=r"U:\w&k(2)\wf g.txt"
    ... convunix(fn) == "/U/w\&k\(2\)/wf\ g.txt"
    True

    '''
    nfn=fn.replace('\\','/').replace(' ',r'\ ').replace('(',r'\(').replace(')',r'\)').replace('&',r'\&')
    rese=re.search('(\w):',nfn)
    if rese:
       nfn = nfn.replace(nfn[:rese.span(0)[1]],rese.expand(r'/\1'))
    return nfn

def html_files(filename):
    '''check whether filename is a saved html file'''
    res = False
    if html_files_suffix + os.sep in filename:
        filename = filename.split(html_files_suffix)[0]
        res = (os.path.exists(filename + '.html')
               or os.path.exists(filename + '.htm'))
    return res

relocates = 'cp mv cpmdate mvmdate'
def remdups(
      scriptfile = None
    , only_same_name = False
    , safe = False
    , keep_in = []
    , keep_out = []
    , comment_out = []
    , html_files_suffix = '_files'
    , hash_only = False
    , exclude_dir = []
    , where_name = None
    , where_file = None
    , relocate = 'copysort'
    ):
    '''makes the program's functionality available to from within python'''
    win32 = sys.platform=='win32'
    s = [ scripfile.name.endswith('.bat'),
          scripfile.name.endswith('.sh')
          ]
    batch,shscript = range(len(s))
    scrpt = s.index(True)
    flnm = [
          lambda fn:  '"' + fn + '"'
          lambda fn: win32 and fn or convunix(fn)
          ]
    rm = [
          'del /F',
          'rm -f'
          ]
    rmdir = [
          'rmdir /S',
          'rm -rf'
          ]
    cmt = [
          "REM "
          "#"
          ]
    cms = cmt[scrpt]

    hashfilename = '.remdups_c.sha265'
    hashfilenames = ['.remdups_'+m+'.'+h for m,h in product('c b d e n'.split(),'sha512 sha384 sha256 sha224 sha1 md5'.split())]
    for h in hashfilenames:
       if os.path.exists(hashfilename):
          hashfilename = h
          break
    _,__,source,method = re.split('_|\.',hashfilename)

    hasher = eval('hashlib.' + method)
    _hash_file = lambda fn: hash_file(fn, source, hasher)

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
        flnms = flnm[scrpt]
        yield rm[scrpt] + ' ' + flnms(filepath)
        filename, ext = os.path.splitext(filepath)
        if '.htm' in ext:
            htmlfiles = filename + html_files_suffix
            if os.path.exists(htmlfiles):
                yield rmdir[scrpt] + ' '+ flnms(htmlfiles)

    def gen_command(tail_same):
        '''yield all remove commands'''
        lenk = lambda x: len(x)
        equal = lambda x: x
        tokeep = keepers + [equal]
        for tail, same in tail_same:
            yield ''
            yield cms+':#' + tail + '{{{'
            # take the shortest path in the smallest set
            keep = sorted(filter(equal,
                [sorted(kp(same), key=lenk) for kp in tokeep]), key=lenk)[0][0]
            for filename in sorted(same):
                comment = ''
                if any([cmnt(filename) for cmnt in comment_outs]):
                    comment = cms+'c#'
                elif filename == keep:
                    comment = cms
                for command in rmcmd(filename):
                    yield comment + command
            yield cms+':#}}}'

    with open(hashfilename,'a+',encoding='utf-8') as hashfile:
        hashlist = Hashlist(re.split(r'\s+', e.strip(), maxsplit=1)
                           for e in hashfile.readlines())

    hashlist.walkhash(_hash_file=_hash_file, exclude_dirs=exclude_dir)

    if not hash_only:
        grps_no, grps_with = hashlist.find_dups(
            only_same_name=only_same_name, safe=safe)

        if where_name:
            output = []
            wheregroups = hashlist.where_name(where_name)
            for wheregroup in wheregroups:
                for where in wheregroup:
                    output.append(where)
                output.append('')
        elif where_file:
            output = hashlist.where_file(where_file)
        else:  # script
            output = []
            if grps_no or grps_with:
                output.append(cms+'## vim: set fdm=marker')
            if grps_no:
                output.append('')
                output.append(cms+'## No Same Tail {{{')
                for line in gen_command(grps_no):
                    output.append(line)
                output.append(cms+'## }}}')
            if grps_with:
                output.append('')
                output.append(cms+'## With Same Tail {{{')
                for line in gen_command(grps_with):
                    output.append(line)
                output.append(cms+'## }}}')

        if scriptfile != None:
            script = '\n'.join(output)
            scriptfile.write(script)

        return output


def args():
    '''parses the arguments and returns a dictionary of them'''
    import argparse

    parser = argparse.ArgumentParser(description = __doc__,
            formatter_class = argparse.ArgumentDefaultsHelpFormatter)

    #script
    parser.add_argument('scriptfile', nargs='?', type=argparse.FileType('w',encoding='utf-8'),
                        default=sys.stdout)
    parser.add_argument(#only_same_name
        '-n', '--only-same-name', action='store_true',
        help='Only consider files with same name')
    parser.add_argument(#safe
        '-s', '--safe', action='store_true',
        help='Do not trust filename+hash, '
             'but do an additional bytewise compare.')
    parser.add_argument(#html_files_suffix
        '-x', '--html-files-suffix', action='store', default='_files',
        help='When saving an html '
        'the files get into a subfolder formed with a suffix to the html file.'
        'User = for suffixes starting with a hyphen, like: -x="-Dateien".')
    parser.add_argument(#keep_in
        '-i', '--keep-in', action='append', default=[],
        help='Add substring to make other files of the duplicates be removed.')
    parser.add_argument(#keep_out
        '-o', '--keep-out', action='append', default=[],
        help='Add substring to make this files of the duplicates be removed.')
    parser.add_argument(#comment_out
        '-c', '--comment-out', action='append', default=[],
        help='Add substring to make the remove command '
        'for the file containing it, be commented out.')
    parser.add_argument(#exclude_dir
        '-e', '--exclude-dir', action='append', default=[],
        help='Exclude such dir names when walking the directory tree.')
    parser.add_argument(#relocate TODO
        '-t', '--relocate', action='store', 
        help='Instead of remove, do move or copy to new root those that would not be removed. Provide either of:'+relocates)
    parser.add_mutually_exclusive_group()
    parser.add_argument(#where_name
        '-w', '--where-name', action='store',
        help='All places for this name, grouped by same hash.')
    parser.add_argument(#where_file
        '-W', '--where-file', action='store',
        help='All places for the hash of this file.')
    parser.add_mutually_exclusive_group()
    parser.add_argument(#hash_only
        '-h','--hash-only', action='store_true',
        help='After updating .remdups_x.y no script is generated.')

    argdict = vars(parser.parse_args())  # exception when using py.test

    return argdict  # pragma: no cover

def main():
    remdups(**args())  # pragma: no cover

if __name__ == '__main__':
    main()

