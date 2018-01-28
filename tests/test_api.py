# -*- coding: utf-8 -*

#py.test test_api.py --cov remdups --cov-report term-missing

import os
import tempfile
import subprocess
import shutil
from glob import glob
from itertools import product
import PIL
from PIL import ImageDraw
try:  # pragma: no cover
    from StringIO import StringIO  # pragma: no cover
except ImportError:  # pragma: no cover
    from io import StringIO  # pragma: no cover
import pytest
from pytest_toolbox import mktree

from remdups import *

def test_haslist_default(tmpworkdir):
  h=Hasher()
  assert h.hashfiles==['.remdups_c.sha256']

def test_haslist_more(tmpworkdir):
  ah = list(product('c b d e n'.split(),'sha512 sha384 sha256 sha224 sha1 md5'.split()))
  lenah = len(ah)
  mktree(tmpworkdir,{remdupsfile(a,h):"" for a,h in ah})
  assert len(os.listdir()) == lenah
  hf = remdupsfile(*ah[0])
  assert os.path.exists(hf)
  h=Hasher()
  h.load_hashes()
  h.hashall()
  with open(hf,'r') as f:
    lns = f.readlines()
  assert len(lns)==0 #.remdups_* ignored

@pytest.fixture
def emptyhashfile(tmpworkdir):
  img = PIL.Image.new('RGB', (100, 100))
  draw = ImageDraw.Draw(img)
  draw.text((10, 10), "img", fill=(255, 0, 0))
  del draw
  img.save('img.jpg','jpeg')
  hf = '.remdups_e.sha256'
  with open(hf,'w'):pass
  shutil.copy2('img.jpg','newimg.jpg')
  os.mkdir('sub')
  [shutil.copy2(x,'sub') for x in glob('*.jpg')]
  return hf

@pytest.fixture
def dups(emptyhashfile):
  rd = RemDups()
  #import pdb; pdb.set_trace()
  rd.hasher.hashall()
  with open(emptyhashfile,'r') as f:
    lns = f.readlines()
  assert len(lns)==4 #.remdups_* ignored
  with pytest.raises(AttributeError):
    rd.with_same_tail
  with pytest.raises(AttributeError):
    rd.no_same_tail
  return rd

@pytest.mark.parametrize('cmd,script',zip(['rm','cp','mv'],['script.sh','script.bat']))
def test_find_dups(dups,cmd,script):
  if cmd!='rm':
    with pytest.raises(ValueError):#see fn2dirfn
      cmds=getattr(dups,cmd)(script=argparse.FileType('w',encoding='utf-8')(script))
  cmds=getattr(dups,cmd)(script=argparse.FileType('w',encoding='utf-8')(script),sort="%y%m/%d%H%M%S")
  assert len(dups.with_same_tail)==0
  assert len(dups.no_same_tail)==1 #script.sh has no duplicate
  tails = [tail for tail, paths in dups.no_same_tail]
  assert not any(tails)
  assert len(dups.no_same_tail[0][1]) == 4
  assert len(cmds) == 11
  anybackslashes = any(['\\' in x for x in cmds])
  if script.endswith('.bat'):
    assert anybackslashes
  else:#.sh
    assert not anybackslashes
  if cmd=='rm':#remove all but one
    assert sum([re.match('^'+dups.comment+'>#',x) and 1 or 0 for x in cmds]) == 1
  else:#copy one and leave the rest
    assert sum([re.match('^'+dups.comment+'>#',x) and 1 or 0 for x in cmds]) == 3
  dups.args.script.close()
  assert os.path.exists(script)
  lns = []
  with open(script,'r') as f:
    lns = f.readlines()
  assert len(lns) == 11

@pytest.fixture
def othertmpdir(request):
  tempdir = tempfile.mkdtemp()
  request.addfinalizer(lambda :shutil.rmtree(tempdir))
  return tempdir

def test_hash_and_write(emptyhashfile,othertmpdir):
  with open(emptyhashfile.replace('256','512'),'w'): pass #two hash files now
  allduplicates = []
  assert othertmpdir != os.getcwd()
  hshr = Hasher()
  for f,duplicates,content in hshr.foreachcontent('.'):
    if duplicates:
      allduplicates.append(f)
    else:
      _,nfd,nff = fn2dirfn(f,"%y%m/%d%H%M%S")
      nfnf = joinp(othertmpdir,nff)
      nfnd= normp(joinp(othertmpdir,nfd))
      os.makedirs(nfnd)
      with open(nfnf,'wb') as nf:
        for buf in content:
          nf.write(buf)
      same = filecmp.cmp(f, nfnf, False)
      assert same
  assert allduplicates==[hshr.relpath(x) for x in ['newimg.jpg', 'sub/img.jpg', 'sub/newimg.jpg']]
  hshr.clear()
  assert len(hshr.path_hash)==0
  allduplicates = []
  for f in hshr.scandir(fromdir=othertmpdir):
    if hshr.duplicates(f):
      allduplicates.append(f)
  assert len(hshr.path_hash)==1
  assert allduplicates==[]

def test_resort(emptyhashfile,othertmpdir):
  with open('.remdups_c.sha256','w'): pass
  resort(othertmpdir,"%y%m/%d_%H%M%S")
  cd = os.getcwd()
  os.chdir(othertmpdir)
  with open('.remdups_c.sha256','w'): pass
  hshr = Hasher()
  assert len([f for f in hshr.scandir(othertmpdir)]) == 1
  os.chdir(cd)


#help(tempfile.mkdtemp)
#help(tempfile.gettempdir)
#help(tempfile.tempdir)

#def test_haslist_default(tmpworkdir):
#  h=Hasher()
#  assert os.path.exists('.remdups_c.sha256')

#hashlist = Hashlist([('ha', 'b/a'), ('ha', 'c/a'), ('ha', 'u/v/a'),
#                     ('hb', 'u/v/y'), ('hb', 'c/x'), ('hb', 'b/a'),
#                     ('hc', 'r/s'),
#                     ('hd', 'g/h/i.html'), ('hd', 'k/h/i.html')])
#
#ochd = os.getcwd()
#
#def setup_module(module):
#    global tmproot
#    tmproot = tempfile.mkdtemp()
#    os.chdir(tmproot)
#    for path, _hash in hashlist.path_hash.items():
#        pdir, pfile = os.path.split(path)
#        try:
#            if pdir:
#                os.makedirs(pdir)
#        except:
#            pass
#        with open(path, 'w') as _file:
#            if path == 'b/a':
#                # same hash but different content simulation
#                img = PIL.Image.new('RGB', (1000, 1000))
#                draw = ImageDraw.Draw(img)
#                draw.text((10, 10), _hash, fill=(255, 0, 0))
#                del draw
#                img.save(path, 'jpeg')
#            else:
#                _file.write(_hash)
#        if '.html' in path:
#            os.makedirs(path[:-5] + '_files')
#            with open(os.path.join(path[:-5] + '_files', 'tst'), 'w') as _file:
#                _file.write('a html data file')
#    subprocess.call(
#        r'find . -not -type d -exec sha256sum {} \;>.remdups_c.sha256', shell=True)
#
#
#def test_hash_file():
#
#    h1 = hash_file('b/a', 'name')
#    h2 = hash_file('b/a', 'namedate')
#    h3 = hash_file('b/a', 'exif')
#    h4 = hash_file('g/h/i.html', 'exif')
#    h5 = hash_file('g/h/i.html', 'content')
#    h6 = hash_file('b/a', 'block')
#
#    assert h1 != h2
#    assert h2 != h3
#    assert h3 != h4
#    assert h4 == h5
#    assert h5 != h6
#
#
#def test_hashlist():
#
#    withoutname, withname = hashlist.find_dups(safe=True)
#    assert 'b/a' not in dict(withname)['a']
#
#    with pytest.raises(ValueError):
#        hashlist.where_file('/a')
#
#    where = hashlist.where_file('k/h')
#    assert set(where) == set(['k/h/i.html', 'g/h/i.html'])
#
#
#def test_remdups():
#
#    remdups(open('b/a'), hashonly=True)
#
#    outfile = StringIO()
#    remdups(open('b/a'), outfile, hashonly=True)
#    outfile.seek(0)
#    assert 'b/a' in outfile.read()
#
#    remdups(hashonly=True, exclude_dir=['k'])
#    assert len(remdups()) > 0
#
#    wherename = remdups(where_name='a')
#    assert set(wherename) == set(['./c/a', './u/v/a', ''])
#
#    wherefile = remdups(where_file='c/a')
#    assert set(wherefile) == set(['./c/a', './u/v/a'])
#
#    outfile = StringIO()
#    remdups(outfile=outfile, keep_in=['a'], keep_out=['y'], comment_out=['u'])
#    outfile.seek(0)
#    res = [ln.strip()
#           for ln in outfile.readlines() if ln.strip() and '####' not in ln]
#    assert '#rm -f "./c/x"' in res
#
#
#def test_args():
#
#    try:
#        args()
#    except:
#        pass
#
#
#def teardown_module(module):
#
#    for path, _hash in hashlist.path_hash.items():
#        try:
#            if '.html' in path:
#                os.remove(os.path.join(path[:-5] + '_files', 'tst'))
#                os.rmdir(path[:-5] + '_files')
#            os.remove(path)
#            pdir, pfile = os.path.split(path)
#            if pdir:
#                os.removedirs(pdir)
#        except:
#            pass
#
#    os.remove('.remdups_c.sha256')
#    os.chdir(ochd)
#    os.rmdir(tmproot)
