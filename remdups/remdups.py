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

   $remdups script.sh
   $remdups script.bat
   $remdups dodo.py

   If the file ends in .sh, cp is used and the file names are in linux format.
   This is usable also on Windows with MSYS, MSYS2 and CYGWIN.

   If the file ends in .bat, Windows commands are used.

   For dodo.py a doit file is created that imports remdups and does all the processing there.
   To execute it doit must be installed.

3. Inspect the script and go back to 2., if necessary.
   Smaller changes to the script can also be done with the editor.

4. execute script

   $./script.sh

'''

import sys
import os
import os.path
import argparse
try:
   from itertools import zip_longest  # pragma: no cover
except ImportError:  # pragma: no cover
   from itertools import izip_longest as zip_longest  # pragma: no cover
import filecmp
import hashlib
from itertools import product
from collections import defaultdict
import re

__version__ = '1.3' #this is also in setup.py
__appname__ = "Remove Duplicate Files"
__author__  = "Roland Puntaier <roland.puntaier@gmail.com>"
__license__ = "The MIT License (MIT)"

_fnencoding = sys.getfilesystemencoding()

def _fnencode(code):
   if sys.version_info[0] == 3:
      return bytes(code, _fnencoding) # pragma: no cover
   else:  # pragma: no cover
      return code  # pragma: no cover

def _encode(s):
   if sys.version_info[0] == 3:
      return bytes(s,encoding='utf-8')# pragma: no cover
   else:  # pragma: no cover
      return s  # pragma: no cover

remdupsfile = lambda a,h: '.remdups_'+a+'.'+h
class Hasher:
   def __init__(self
         ,startdir='.'
         ,exclude_dir=[]
         ):
      self.hashfiles = []
      hashfilenames = [remdupsfile(a,h) for a,h in product('c b d e n'.split(),'sha512 sha384 sha256 sha224 sha1 md5'.split())]
      for h in hashfilenames:
         if os.path.exists(h):
            self.hashfiles.append(h)
      if not self.hashfiles:
         defaulthashfile = '.remdups_c.sha256'
         with open(defaulthashfile,'w'): pass
         self.hashfiles.append(defaulthashfile)
      #self.hashfiles
      self.hashes2write = defaultdict(list)
      self.startdir=startdir
      self.exclude_dir = exclude_dir
      self.path_hash = defaultdict(str)
      self.loadhashes()
      self.walkhashes()
      self.updatehashfiles()
      self.makehashpaths()
   def updatehashfiles(self):
      for i,hfn in enumerate(self.hashfiles):
         if len(self.hashes2write[i]) > 0:
            with open(hfn,'a',encoding='utf-8') as hashfile:
               hashfile.writelines(['{}\t{}\n'.format(h, p) for h,p in self.hashes2write[i]])
      self.hashes2write = defaultdict(list)
   def makehashpaths(self):
      self.hash_paths = defaultdict(list)
      for apth, ahsh in self.path_hash.items():
         self.hash_paths[ahsh].append(apth)
   def loadhashes(self):
      for hfn in self.hashfiles:
         with open(hfn,'r',encoding='utf-8') as hashfile:
            for e in hashfile.readlines():
               p,h = re.split(r'\s+', e.strip(), maxsplit=1)
               self.path_hash[p]+=h #combine hashes from different .remdups_x.y
   def walkhashes(self):
      for root, dirs, files in os.walk(self.startdir):
         for name in files:
            path = os.path.join(root, name)
            if path not in self.path_hash:
               self(path)
            for exclude in self.exclude_dir:
               if exclude in dirs:
                  dirs.remove(exclude)
   def __call__(self,path):
      #path='__init__.py'
      blocksize = filecmp.BUFSIZE
      hashers = dict()
      sm = [[s,eval('hashlib.' + m)()] for hf in self.hashfiles for s,m in [re.split('_|\.',hf)[2:]]]
      if any([s.startswith('e') for s,m in sm]):#exif
         try:
            from PIL import Image
            img = Image.open(path)
            exif_data = _encode(str(img._getexif()))
            #exif_data = b"{'a':''}",len(exif_data)
            if len(exif_data) < 8:
               raise ValueError()
            for s,m in sm:
               if s.startswith('e'):
                  m.update(exif_data)
         except:#if file is not a pic of no exif data
            for i in range(len(sm)):
               if sm[i][0].startswith('e'):
                  sm[i][0] = 'c'
      if any([s.startswith('c') or s.startswith('b') for s,m in sm]):#content,block
         with open(path, 'rb') as _file:
            #_file=open(path,'rb')
            #_file.close()
            buf = _file.read(blocksize)
            while len(buf) > 0:
               for s,m in sm:
                  #s,m=sm[0]
                  if s.startswith('c') or s.startswith('b'):
                     m.update(buf)
               if not any([s.startswith('c') for s,m in sm]):#no content
                  break
               buf = _file.read(blocksize)
      if any([s.startswith('n') for s,m in sm]):#name
         name = _fnencode(os.path.split(path)[1])
         for s,m in sm:
            if s.startswith('n'):
               m.update(name)
      if any([s.startswith('d') for s,m in sm]):#modification date
         mtime = _encode(str(os.path.getmtime(path)))
         for s,m in sm:
            if s.startswith('d'):
               m.update(mtime)
      hshs = [m.hexdigest() for s,m in sm]
      self.path_hash[path] = ''.join(hshs)
      for i,hsh in enumerate(hshs):
         #i,hsh = 0,hshs[0]
         self.hashes2write[i].append((hsh,path))

def _same_tail(paths,sep=os.sep):
   '''return common tail of paths if any
   >>> paths = ['b/a', 'c/a', 'u/v/a']
   >>> _same_tail(paths,sep='/')
   'a'
   >>> paths = ['b/x', 'c/x', 'u/v/y']
   >>> _same_tail(paths)
   ''

   '''
   spathreversed = [list(reversed(p.split(sep))) for p in paths]
   allsame = lambda e: all([e[0] == x for x in e])
   _sametail = []
   for pathentry in zip_longest(*spathreversed):
      if allsame(pathentry):
         _sametail.append(pathentry[0])
      else:
         break
   savejoin = lambda *x: os.path.join(*x) if x else ''
   return savejoin(*reversed(_sametail))


def _convunix(fn):
   '''
   >>> fn=r"U:\w&k(2)\wf g.txt"
   ... _convunix(fn) == "/U/w\&k\(2\)/wf\ g.txt"
   True

   '''
   nfn=fn.replace('\\','/').replace(' ',r'\ ').replace('(',r'\(').replace(')',r'\)').replace('&',r'\&')
   rese=re.search('(\w):',nfn)
   if rese:
      nfn = nfn.replace(nfn[:rese.span(0)[1]],rese.expand(r'/\1'))
   return nfn

def _html_files(filename):
   '''check whether filename is a saved html file'''
   res = False
   if html_files_suffix + os.sep in filename:
      filename = filename.split(html_files_suffix)[0]
      res = (os.path.exists(filename + '.html')
            or os.path.exists(filename + '.htm'))
      return res

def _genout(output):
   for grp in output:
      if isinstance(grp,list):
         for fl in grp:
            yield fl
         yield ''
      else:
         yield grp
   return output

class RemDups:

   def __init__(self, args):
      self.args = args
      self.hasher = Hasher(
              startdir = '.' if 'fromdir' not in args else args.fromdir,
              exclude_dir = [] if 'exclude_dir' not in args else args.exclude_dir
            )

      scriptn = args.script.name
      #scriptn = 'xx'
      win32 = sys.platform=='win32'
      s = [ 
            scriptn.endswith('.sh'),
            scriptn.endswith('.bat'),
            scriptn.endswith('dodo.py')
            ]
      if not any(s): s[win32] = True

      batch,sh,dodo = range(len(s))
      self.scrpt = s.index(True)
      self.flnm = [
            lambda fn: win32 and _convunix(fn) or fn,
            lambda fn:  '"' + fn + '"',
            lambda fn:  '"' + fn + '"',
            ]
      self._rm = [
            'rm -f',
            'del /F',
            'remove'
            ]
      self._rmdir = [
            'rm -rf',
            'rmdir /S',
            'rmtree'
            ]
      self._cp = [
            'cp',
            'copy',
            'copy2'
            ]
      self._mv = [
            'mv',
            'move',
            'move'
            ]
      self._cmt = [
            "#",
            "REM ",
            "#"
            ]

      self.comment_outs = [_html_files]
      for cmnt in args.comment_out:
         self.comment_outs.append(lambda x, c=cmnt: c in x)

      self.keepers = []
      for keepin in args.keep_in:
         self.keepers.append(lambda values: filter(
            lambda x, k=keepin: k in x, values))
         for keepout in args.keep_out:
            self.keepers.append(lambda values: filter(
               lambda x, k=keepout: k not in x, values))

      if not self.args.hash_only:
         self.find_dups()

   def find_dups(self):
      '''returns groups of same files tuple (no same name, with same name)
      '''
      dups = [paths for h, paths in self.hasher.hash_paths.items() if len(paths) > 1]

      def safe_cmp(tail_files):
         '''form groups based on bytewise comparison'''
         for tail, paths in tail_files:
            cnt = 0
            while len(paths) > 1:
               this, new = [], []
               first = paths[0]
               this.append(first)
               for other in paths[1:]:
                  try:
                     same = filecmp.cmp(first, other, False)
                  except (OSError, IOError): # pragma no cover
                     same = True # pragma no cover
                  if same:
                     this.append(other)
                  else:
                     new.append(other)
               if len(this) > 1:
                  yield (('group {}: '.format(cnt) if cnt else '') + tail, this)
                  cnt += 1
               paths = new

      tail_paths = [(_same_tail(paths), paths) for paths in dups]
      self.no_same_tail = None
      if not self.args.only_same_name:
         self.no_same_tail = [(tail, paths)
               for tail, paths in tail_paths if tail == '']
         if self.args.safe:
            self.no_same_tail = list(safe_cmp(self.no_same_tail))
      self.with_same_tail = [(tail, paths)
            for tail, paths in tail_paths if tail != '']
      if self.args.safe:
         self.with_same_tail = list(safe_cmp(self.with_same_tail))


   def rm(self):
      "remove duplicate files"
      def rmcmd(filepath):
         '''yield one remove command'''
         flnms = self.flnm[self.scrpt]
         yield self._rm[self.scrpt] + ' ' + flnms(filepath)
         filename, ext = os.path.splitext(filepath)
         if '.htm' in ext:
            htmlfiles = filename + self.args.html_files_suffix
            if os.path.exists(htmlfiles):
               yield self._rmdir[self.scrpt] + ' '+ flnms(htmlfiles)

      def gen_command(tail_same):
         '''yield all remove commands'''
         lenk = lambda x: len(x)
         equal = lambda x: x
         tokeep = self.keepers + [equal]
         cms = self._cmt[self.scrpt]
         for tail, same in tail_same:
            yield ''
            yield cms+':#' + tail + '{{{'
            # take the shortest path in the smallest set
            keep = sorted(filter(equal,
               [sorted(kp(same), key=lenk) for kp in tokeep]), key=lenk)[0][0]
            for filename in sorted(same):
               comment = ''
               if any([cmnt(filename) for cmnt in self.comment_outs]):
                  comment = cms+'c#'
               elif filename == keep:
                  comment = cms
               for command in rmcmd(filename):
                  yield comment + command
            yield cms+':#}}}'

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

      if self.args.script != None:
         self.args.script.write('\n'.join([o for o in _genout(output)]))

      return output

   def cp(self):
      "copy duplicate files from other directory to here, ignoring duplicates"
      pass
   def mv(self):
      "move files from other directory to here, ignoring duplicates"
      pass
   def dupsoftail(self):
      "duplicates groups having the provided tail"
      output = [paths for t, paths in self.with_same_tail if t.endswith(self.args.tail)]
      if self.args.script != None:
         self.args.script.write('\n'.join([o for o in _genout(output)]))
      return output
   def dupsof(self):
      "duplicates of a provided file name or substring of"
      try:
         _hash = self.hasher.path_hash[self.args.substr]
      except KeyError:
         _hash = [h for p, h in self.path_hash.items() if self.args.substr in p]
         if not _hash or len(_hash) > 1:
            raise ValueError('Path does not (uniquely) define a file')
         _hash = _hash[0]
      output = self.hasher.hash_paths[_hash]
      if self.args.script != None:
         self.args.script.write('\n'.join([o for o in _genout(output)]))
      return output

def rm(args):
   remdups = RemDups(args)
   remdups.rm(args)
def cp(args):
   remdups = RemDups(args)
   remdups.cp(args)
def mv(args):
   remdups = RemDups(args)
   remdups.mv(args)
def dupsoftail(args):
   remdups = RemDups(args)
   remdups.dupsoftail(args)
def dupsof(args):
   remdups = RemDups(args)
   remdups.dupsof(args)

def set_default_subparser(parser, argv, name):
   subparser_found = False
   for arg in argv[1:]:
      if arg in ['-h', '--help']:  # global help if no subparser
         break
   else:
      for x in parser._subparsers._actions:
        if not isinstance(x, argparse._SubParsersAction):
           continue
        for sp_name in x._name_parser_map.keys():
           if sp_name in argv[1:]:
              subparser_found = True
      if not subparser_found:
         argv.insert(1, name)

def parse_args(argv):
   """parses the arguments and returns a dictionary of them
   """
   parser = argparse.ArgumentParser(prog='remdups',description = __doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
   subparsers = parser.add_subparsers(help='rm is default commnad. "remdups <command> --help" for help on the command. ',dest='cmd')
   crm = subparsers.add_parser('rm',help=rm.__doc__)
   crm.set_defaults(func=rm)
   cmv = subparsers.add_parser('mv',help=mv.__doc__)
   cmv.set_defaults(func=mv)
   ccp = subparsers.add_parser('cp',help=cp.__doc__)
   ccp.set_defaults(func=cp)
   cdupsof = subparsers.add_parser('dupsof',help=dupsof.__doc__)
   cdupsof.add_argument('substr',action='store')
   cdupsof.set_defaults(func=dupsof)
   cdupsoftail = subparsers.add_parser('dupsoftail',help=dupsoftail.__doc__)
   cdupsoftail.add_argument('tail',action='store')
   cdupsoftail.set_defaults(func=dupsoftail)
   for p in [crm,cmv,ccp]:
      p.add_argument('-s','--script', action="store", type=argparse.FileType('w',encoding='utf-8'), required=True,
            help='Write to specified script. Required, because name of script determines format.')
      p.add_argument(#only_same_name
            '-n', '--only-same-name', action='store_true',
            help='Only consider files with same name.')
      p.add_argument(#safe
            '-f', '--safe', action='store_true',
            help='Do not trust filename+hash, '
            'but do an additional bytewise compare.')
      p.add_argument(#html_files_suffix
            '-x', '--html-files-suffix', action='store', default='_files',
            help='When saving an html '
            'the files get into a subfolder formed with a suffix to the html file.'
            'User = for suffixes starting with a hyphen, like: -x="-Dateien".')
      p.add_argument(#keep_in
            '-i', '--keep-in', action='append', default=[],
            help='Add substring to make other files of the duplicates be removed.')
      p.add_argument(#keep_out
            '-o', '--keep-out', action='append', default=[],
            help='Add substring to make this files of the duplicates be removed.')
      p.add_argument(#comment_out
            '-c', '--comment-out', action='append', default=[],
            help='Add substring to make the remove command '
            'for the file containing it, be commented out.')
      p.add_argument(#exclude_dir
            '-e', '--exclude-dir', action='append', default=[],
            help='Exclude such dir names when walking the directory tree.')
      p.add_argument(#hash_only
            '-y','--hash-only', action='store_true',
            help='After updating .remdups_x.y no script is generated.')
   for p in [cmv,ccp]:
      p.add_argument('--sort',action='store',default='%y%m|%d%H%M%S',help="Resort to new folders. | separates dir and name. Else see https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior")
      p.add_argument('fromdir',action='store')
   set_default_subparser(parser,argv,'rm')
   return parser.parse_args(argv[1:])

if __name__ == '__main__':
   parse_args(sys.argv)
