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
Usage:

1. Create file hash list .remdups_c.sha256 in current directory:

     $remdups
     $remdups update

   New files are added to .remdups_x.y. To rehash all files, first remove .remdups_*.

   Do 

      $cat > .remdups_c.sha512

   to determine the hash method in advance. More methods are possible.
   All of .remdups_{c,b,d,e,n}.{sha512, sha384, sha256, sha224, sha1, md5} present, are considered.

   {'c': 'content', 'b': 'block', 'd': 'date', 'e': 'exif', 'n': 'name'}

2. Make a script with rm, mv, cp commands to current directory.
   It can be repeated with different options until the script is good.

   $remdups script.sh
   $remdups mv script.bat
   $remdups cp dodo.py

   If the file ends in .sh, cp is used and the file names are in linux format.
   This is usable also on Windows with MSYS, MSYS2 and CYGWIN.

   If the file ends in .bat, Windows commands are used.

   For dodo.py a doit file is created that imports remdups and does all the processing there.
   To execute it doit must be installed.

3. Inspect the script and go back to 2., if necessary.
   Changes to the script can also be done with the editor.

4. execute script

   $./script.sh

'''

import sys
import os
import os.path
import argparse
import time
try:
   from itertools import zip_longest  # pragma: no cover
except ImportError:  # pragma: no cover
   from itertools import izip_longest as zip_longest  # pragma: no cover
import filecmp
import hashlib
from itertools import product
from collections import defaultdict
import re
from fnmatch import fnmatch
normp = os.path.normpath
joinp = os.path.join
#normp(r'ax\ay/az\f')#ax\ay\az\f on windows else all /
#normp(r'**\az/*')#**\az\*
#fnmatch(normp('ax/ay/az/f'),normp('ax/*/az/*'))#True
#fnmatch(normp('ax/ay/az/f'),normp('ax/*/f'))#True

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
   def __init__(self):
      self.hashfiles = []
      hashfilenames = [remdupsfile(a,h) for a,h in product('c b d e n'.split(),'sha512 sha384 sha256 sha224 sha1 md5'.split())]
      for h in hashfilenames:
         if os.path.exists(h):
            self.hashfiles.append(h)
      if not self.hashfiles:
         defaulthashfile = '.remdups_c.sha256'
         with open(defaulthashfile,'w'): pass
         self.hashfiles.append(defaulthashfile)
      self.clear()
   def load_hashes(self):
      for hfn in self.hashfiles:
         with open(hfn,'r',encoding='utf-8') as hashfile:
            for e in hashfile.readlines():
               p,h = re.split(r'\s+', e.strip(), maxsplit=1)
               self.path_hash[p]+=h #combine hashes from different .remdups_x.y
      self._make_hash_paths()
   @staticmethod
   def relpath(path):
      return normp(os.path.relpath(path))
   def foreachcontent(self,*k,**kw):
      "yields (f,duplicates,content). send true to cleare or false to add to hashes."
      kw['keepcontent']=[]
      for f in self.scandir(*k,**kw):
         duplicates = self.duplicates(f)
         yield (f,duplicates,kw['keepcontent'])
         if duplicates:
            self.clear(f)
         else:
            self.update_hashfiles()
         kw['keepcontent']=[]
   def hashall(self,*k,**kw):
      "Finds files not yet hashed and adds their hashes to the .remdups_* files"
      for x in self.scandir(*k,**kw): pass
   def scandir(self
         ,fromdir='.'
         ,filter=[]
         ,exclude=[]
         ,keepcontent=None
         ):
      fok = [normp(f) for f in filter]
      no = [normp(f) for f in exclude if not f.startswith('!')]+[r".remdups_*"]
      yes = [normp(f[1:]) for f in exclude if f.startswith('!')]
      nfromdir = self.relpath(fromdir)
      for root, dirs, files in os.walk(nfromdir):
         drfl = [(0,x) for x in files]+[(1,y) for y in dirs]
         newdirs=[]
         for dir,name in drfl:
            path = joinp(root, name)
            repth = self.relpath(path)
            if any([fnmatch(repth,f) for f in no]) and not any([fnmatch(path,f) for f in yes]):
               continue
            if not (any([fnmatch(repth,f) for f in fok]) or not fok):
               continue
            if not dir:
               if repth not in self.path_hash:
                  self.hash(repth,keepcontent)
                  yield repth
            else:
               newdirs.append(name)
         dirs[:]=newdirs
         self.update_hashfiles(fromdir)
   def update_hashfiles(self,fromdir='.'):
      nfromdir = self.relpath(fromdir)
      #// or \\ to know how to construct tree here for cp and mv
      if nfromdir == '.':
         #nfromdir='.'
         fixfromdir = lambda p: p
      else:
         #nfromdir=joinp(*"../../../x/y".split('/'))
         fixfromdir=lambda p: p.startswith(nfromdir) and nfromdir+os.sep*2+p[len(nfromdir):].strip(os.sep) or p
      #p=joinp(*"../../../x/y/z/n".split('/'))
      #fixfromdir(p)
      for i,hfn in enumerate(self.hashfiles):
         if len(self.hashes2write[i]) > 0:
            with open(hfn,'a',encoding='utf-8') as hashfile:
               hashfile.writelines(['{}\t{}\n'.format(h, fixfromdir(p)) for h,p in self.hashes2write[i]])
      self.hashes2write = defaultdict(list)
   def _make_hash_paths(self):
      for apth, ahsh in self.path_hash.items():
         self.hash_paths[ahsh].append(apth)
   def duplicates(self,f_or_substr):
      try:
         _hash = self.path_hash[f_or_substr]
      except KeyError:
         _hash = [h for p, h in self.path_hash.items() if f_or_substr in p]
         if not _hash or len(_hash) > 1:
            raise ValueError('Path does not (uniquely) define a file')
         _hash = _hash[0]
      return [p for p in self.hash_paths[_hash] if f_or_substr not in p]
   def clear(self,repth=None):
      if repth:
         _hash = self.path_hash[repth]
         del self.path_hash[repth]
         pths = self.hash_paths[_hash]
         i = pths.index(repth)
         del pths[i]
         for h in range(len(self.hashfiles)):
            w = self.hashes2write[h]
            ii = [i for i,(_,p) in enumerate(w) if p == repth]
            for i in reversed(ii):
               del w[i]
      else:
         self.hashes2write = defaultdict(list)
         self.path_hash = defaultdict(str)
         self.hash_paths = defaultdict(list)
   def hash(self,repth,keepcontent=None):
      #repth='__init__.py'
      blocksize = filecmp.BUFSIZE
      hashers = dict()
      sm = [[s,getattr(hashlib,m)()] for hf in self.hashfiles for s,m in [re.split('_|\.',hf)[2:]]]
      if any([s.startswith('e') for s,m in sm]):#exif
         try:
            from PIL import Image
            img = Image.open(repth)
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
         with open(repth, 'rb') as _file:
            #_file=open(repth,'rb')
            #_file.close()
            buf = _file.read(blocksize)
            if keepcontent!=None: 
               keepcontent.append(buf)
            while len(buf) > 0:
               for s,m in sm:
                  #s,m=sm[0]
                  if s.startswith('c') or s.startswith('b'):
                     m.update(buf)
               if not any([s.startswith('c') for s,m in sm]):#no content
                  break
               buf = _file.read(blocksize)
               if keepcontent!=None: 
                  keepcontent.append(buf)
      if any([s.startswith('n') for s,m in sm]):#name
         name = _fnencode(os.repth.split(repth)[1])
         for s,m in sm:
            if s.startswith('n'):
               m.update(name)
      if any([s.startswith('d') for s,m in sm]):#modification date
         mtime = _encode(str(os.repth.getmtime(repth)))
         for s,m in sm:
            if s.startswith('d'):
               m.update(mtime)
      hshs = [m.hexdigest() for s,m in sm]
      ahsh = ''.join(hshs)
      self.path_hash[repth] = ahsh
      self.hash_paths[ahsh].append(repth)
      for i,hsh in enumerate(hshs):
         #i,hsh = 0,hshs[0]
         self.hashes2write[i].append((hsh,repth))

def resort(newdir,scheme="%y%m/%d_%H%M%S"):
   "resort according to scheme in newdir, ignoring duplicates"
   hasher = Hasher()
   for f,duplicates,content in hasher.foreachcontent('.'):
      if not duplicates:
         _,newd,newf = fn2dirfn(f,scheme)
         othernewf = joinp(newdir,newf)
         othernewd = normp(joinp(newdir,newd))
         os.makedirs(othernewd)
         with open(othernewf,'wb') as nf:
            for buf in content:
               nf.write(buf)

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
   savejoin = lambda *x: joinp(*x) if x else ''
   return savejoin(*reversed(_sametail))

def _convunix(fn):
   '''
   >>> fn=r"U:\w&k(2)\wf g.txt"
   ... _convunix(fn) == "/U/w\&k\(2\)/wf\ g.txt"
   True

   '''
   nfn=fn.replace('\\','/')
   rese=re.search('(\w):',nfn)
   if rese:
      nfn = nfn.replace(nfn[:rese.span(0)[1]],rese.expand(r'/\1'))
   #https://unix.stackexchange.com/questions/347332/what-characters-need-to-be-escaped-in-files-without-quotes
   #instead of .replace(' ',r'\ ').replace('(',r'\(').replace(')',r'\)').replace('&',r'\&')...
   nfn = "'"+nfn.replace("'","'\\''")+"'"
   return nfn

def fn2dirfn(fn,srt=''): 
   """
   >>> fn2dirfn('../a//b/c'.replace('/',os.sep))==('..\\a\\\\b\\c', '.\\b', '.\\b\\c')
   True
   >>> srt = "%y%m/%d%H%M%S"
   ... df=fn2dirfn(os.listdir()[0],srt)
   ... len(df)==3
   True
   """
   _,ext = os.path.splitext(fn)
   treesep = os.sep*2
   if srt:
      mtime = time.localtime(os.stat(fn).st_mtime)
      #time.strftime(srt,time.struct_time((2018,3,2,9,8,7,6,5,4)))
      newfn = joinp('.',normp(time.strftime(srt,mtime))+ext)
   elif treesep in fn:
      newfn = joinp('.',fn.split(treesep)[1])
   else:
      raise ValueError("Not specified where to copy/move, here.")
   newdir,_ = os.path.split(newfn)
   return fn,newdir,newfn

class RemDups:

   def __init__(self):
      self.hasher = Hasher()
      self.hasher.load_hashes()

   def init_command(self,**args):
      win32 = sys.platform=='win32'
      self.args = argparse.Namespace(**args)
      try:
         scriptn = self.args.script.name
         s = [ 
            scriptn.endswith('.sh'),
            scriptn.endswith('.bat'),
            scriptn.endswith('dodo.py')
            ]
      except:
         s = [0]*3
      if not any(s): s[win32] = 1

      #from shutil import *
      #from os import *
      #xmove = lambda x,y: makedirs(y+os.sep,exist_ok=True) and copy2(x,y)
      #xcopy = lambda x,y: makedirs(y+os.sep,exist_ok=True) and move(x,y)
      #xmove('tmp.txt','a/b/c')
      #batch,sh,dodo = range(len(s))
      scripttype = s.index(True)
      formatpath = [
            lambda fn: win32 and _convunix(fn) or fn,
            lambda fn:  '"' + fn + '"',
            lambda fn:  'r"' + fn + '"',
            ]
      filecommand = {
         "rm": [
            'rm -f {0}',
            'del /F/Q {0}',
            'remove({0})'
            ],
         "cp": [#0,1,2=fn, dest dir, dest full pth
            'mkdir -p {1} & cp {0} {2}',
            'xcopy /Y {0} {2}',
            'makedirs({1},exist_ok=True);copy2({0},{2})'
            ],
         "mv": [
            'mkdir -p {1} & mv {0} {2}',
            'mkdir {1} & move /Y {0} {2}',
            'makedirs({1},exist_ok=True);move({0},{2})'
            ]
         }
      dircommand = {
         "rm": [
            'rm -rf {0}',
            'rmdir /S/Q {0}',
            'rmtree({0})'
            ],
         "cp": [
            'cp -r {0} {2}',
            'xcopy /I/Y/S {0} {2}',
            'copytree({0},{2})'
            ],
         "mv": [
            'mv {0} {2}',
            'move /Y {0} {2}\\',
            'move({0},{2})'
            ]
         }
      comment = [
            "#",
            "REM ",
            "#"
            ]
      #from string import Template
      #help(Template)
      #tmp=Template("cp ${p} ${q}").substitute(p=fixfromdir(p),q=fixfromdir(p).split(os.sep*2)[1])
      #dir(tmp)

      self.getarg = lambda x,default=[]: x in self.args and getattr(self.args,x) or default

      srt = self.getarg('sort','')
      if self.args.cmd == 'rm':
         self.filecommand = lambda f: filecommand[self.args.cmd][scripttype].format(formatpath[scripttype](f))
         self.dircommand = lambda d: dircommand[self.args.cmd][scripttype].format(formatpath[scripttype](af))
      else:
         self.filecommand = lambda f: filecommand[self.args.cmd][scripttype].format(
               *[formatpath[scripttype](af) for af in fn2dirfn(f,srt)]
               )
         self.dircommand = lambda d: dircommand[self.args.cmd][scripttype].format(
               *[formatpath[scripttype](af) for af in fn2dirfn(f,srt)]
               )
      self.comment = comment[scripttype]

      self.comment_outs = [self._html_files]
      comment_out = self.getarg('comment_out')
      for cmnt in comment_out:
         self.comment_outs.append(lambda x, c=cmnt: c in x)

      self.keepers = []
      keep_in = self.getarg('keep_in')
      keep_out = self.getarg('keep_out')
      for keepin in keep_in:
         self.keepers.append(lambda values: filter(
            lambda x, k=keepin: k in x, values))
         for keepout in keep_out:
            self.keepers.append(lambda values: filter(
               lambda x, k=keepout: k not in x, values))

   def find_dups(self):
      '''returns groups of same files tuple (no same name, with same name)
      If not all in the dups grup same tail, then this is no same tail.
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
      only_same_name = self.getarg('only_same_name')
      safe = self.getarg('safe')
      if not only_same_name:
         self.no_same_tail = [(tail,paths) for tail, paths in tail_paths if not tail]
         if safe:
            self.no_same_tail = list(safe_cmp(self.no_same_tail))
      self.with_same_tail = [(tail, paths)
            for tail, paths in tail_paths if tail != '']
      if safe:
         self.with_same_tail = list(safe_cmp(self.with_same_tail))

   def _html_files(self,filename):
      '''check whether filename is a saved html file'''
      res = False
      html_files_suffix = self.getarg('html_files_suffix','_files')
      if html_files_suffix + os.sep in filename:
         filename = filename.split(html_files_suffix)[0]
         res = (os.path.exists(filename + '.html')
               or os.path.exists(filename + '.htm'))
         return res

   def gen_command(self,tail_paths):
      '''yield all commands'''
      c = self.comment
      lenk = lambda x: len(x)
      equal = lambda x: x
      tokeep = self.keepers + [equal]
      html_files_suffix = self.getarg('html_files_suffix')
      for tail, paths in tail_paths:
         yield ''
         yield c+':#' + tail + '{{{'
         # take the shortest path in the smallest set
         keep = sorted(filter(equal,
            [sorted(kp(paths), key=lenk) for kp in tokeep]), key=lenk)[0][0]
         for pth in sorted(paths):
            if self.args.cmd == 'rm':
               cc = ''
            else:
               cc = c+'>#'
            if pth == keep:
               if self.args.cmd == 'rm':
                  cc = c+'>#'
               else:
                  cc = ''
            if any([cmnt(pth) for cmnt in self.comment_outs]):
               cc = c+'c#'
            yield cc+self.filecommand(pth)
            filename, ext = os.path.splitext(pth)
            if '.htm' in ext:
               htmlfiles = filename + html_files_suffix
               if os.path.exists(htmlfiles):
                  yield cc+self.dircommand(htmlfiles)
         yield c+':#}}}'

   def out(self,output):
      def _genout(output):
         for grp in output:
            if isinstance(grp,list):
               for fl in grp:
                  yield fl
               yield ''
            else:
               yield grp
      if 'script' in self.args and self.args.script != None:
         self.args.script.write('\n'.join([o for o in _genout(output)]))

   def commands(self):
      self.find_dups()
      c = self.comment
      cmds = []
      if self.no_same_tail or self.with_same_tail:
         cmds.append(c+'## vim: set fdm=marker')
      if self.no_same_tail:
         cmds.append('')
         cmds.append(c+'## No Same Tail {{{')
         for line in self.gen_command(self.no_same_tail):
            cmds.append(line)
         cmds.append(c+'## }}}')
      if self.with_same_tail:
         cmds.append('')
         cmds.append(c+'## With Same Tail {{{')
         for line in self.gen_command(self.with_same_tail):
            cmds.append(line)
         cmds.append(c+'## }}}')
      self.out(cmds)
      return cmds

   def rm(self,**args):
      "remove duplicate files"
      args['cmd'] = 'rm'
      self.init_command(**args)
      return self.commands()
   def cp(self,**args):
      "copy duplicate files from other directory to here, ignoring duplicates"
      args['cmd'] = 'cp'
      self.init_command(**args)
      return self.commands()
   def mv(self,**args):
      "move files from other directory to here, ignoring duplicates"
      args['cmd'] = 'mv'
      self.init_command(**args)
      return self.commands()
   def dupsoftail(self,**args):
      "duplicates having the provided tail"
      args['cmd'] = 'dupsoftail'
      self.init_command(**args)
      self.find_dups()
      output = [paths for t, paths in self.with_same_tail if t.endswith(self.args.tail)]
      self.out(output)
      return output
   def dupsof(self,**args):
      "duplicates of a provided file name or substring"
      args['cmd'] = 'dupsof'
      self.init_command(**args)
      output=self.hasher.duplicates(self.args.substr)
      self.out(output)
      return output

def update(args):
   remdups = RemDups()
   remdups.hasher.hashall(
         args.fromdir
         ,args.filter
         ,args.exclude
         )
def rm(args):
   remdups = RemDups()
   return remdups.rm(**vars(args))
def cp(args):
   remdups = RemDups()
   return remdups.cp(**vars(args))
def mv(args):
   remdups = RemDups()
   return remdups.mv(**vars(args))
def dupsoftail(args):
   remdups = RemDups()
   return remdups.dupsoftail(**vars(args))
def dupsof(args):
   remdups = RemDups()
   return remdups.dupsof(**vars(args))

def parse_args(argv):
   """parses the arguments and returns a dictionary of them
   """
   parser = argparse.ArgumentParser(prog='remdups',description = __doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
   subparsers = parser.add_subparsers(help='*update* is default commnad. "remdups <command> --help" for help on the command. ',dest='cmd')
   cupdate = subparsers.add_parser('update',help=Hasher.hashall.__doc__)
   cupdate.set_defaults(func=update)
   cupdate.add_argument(#filter
         '-f', '--filter', action='append', default=[],
         help='Filter paths of such pattern. https://docs.python.org/3.6/library/fnmatch.html')
   cupdate.add_argument(#exclude
         '-e', '--exclude', action='append', default=[],
         help='Exclude paths of such pattern. ! in front will not exclude it. https://docs.python.org/3.6/library/fnmatch.html')
   cupdate.add_argument('fromdir',nargs='?',default='.',help="directory to take files form")
   crm = subparsers.add_parser('rm',help=RemDups.rm.__doc__)
   crm.set_defaults(func=rm)
   cmv = subparsers.add_parser('mv',help=RemDups.mv.__doc__)
   cmv.set_defaults(func=mv)
   ccp = subparsers.add_parser('cp',help=RemDups.cp.__doc__)
   ccp.set_defaults(func=cp)
   for p in [crm,cmv,ccp]:
      p.add_argument('-s','--script', action="store", type=argparse.FileType('w',encoding='utf-8'), required=True,
            help='Write to specified script. Required, because name of script determines the command format.')
      p.add_argument(#only_same_name
            '-n', '--only-same-name', action='store_true',
            help='Only check files with same name (same tail) for duplicates.')
      p.add_argument(#safe
            '-a', '--safe', action='store_true',
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
   for p in [cmv,ccp]:
      p.add_argument('--sort',action='store',default='',
            help="Resort to new folders, like e.g. %y%m/%d%H%M%S. \
                  See https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior".replace('%','%%'))
   cdupsof = subparsers.add_parser('dupsof',help=RemDups.dupsof.__doc__)
   cdupsof.add_argument('substr',nargs='?',help="tail substring of path")
   cdupsof.set_defaults(func=dupsof)
   cdupsoftail = subparsers.add_parser('dupsoftail',help=RemDups.dupsoftail.__doc__)
   cdupsoftail.add_argument('substr',nargs='?',help="substring of path")
   cdupsoftail.set_defaults(func=dupsoftail)
   def set_default_subparser(name):
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
   set_default_subparser('update')
   return parser.parse_args(argv[1:])

if __name__ == '__main__':
   parse_args(sys.argv)
