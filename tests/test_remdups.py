# -*- coding: utf-8 -*

#py.test --cov remdups --cov-report term-missing

import os
import tempfile
import subprocess
import shutil
from itertools import product
import PIL
import piexif
from PIL import ImageDraw
try:  # pragma: no cover
    from StringIO import StringIO  # pragma: no cover
except ImportError:  # pragma: no cover
    from io import StringIO  # pragma: no cover
import pytest
#from pytest_toolbox import mktree

from remdups import *


##fixtures

#https://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/EXIF.html
someexif={33434: (1, 382), 33437: (200, 100), 34850: 2, 34855: 50, 36864: b'0210',
    36867: b'2017:11:02 14:03:36', 36868: b'2017:11:02 14:03:36', 37121:
    b'\x01\x02\x03\x00', 37377: (85774, 10000), 37378: (200, 100), 37379: (0,
      1), 37380: (0, 1000000), 37383: 1, 37384: 1, 37385: 0, 37386: (3790,
        1000), 37500: b'M[16] [80,1] [d0,ca]\x00', 37510:
      b'ASCII\x00\x00\x00Hisilicon K3\x00', 37520: b'017511', 37521: b'017511',
      37522: b'017511', 40960: b'0100', 40961: 1, 40962: 2336, 40963: 4160,
      40965: 942, 41495: 2, 41728: b'\x03', 41729: b'\x01', 41985: 1, 41986: 0,
      41987: 0, 41988: (100, 100), 41989: 28, 41990: 0, 41991: 0, 41992: 0,
      41993: 0, 41994: 0, 41996: 0}

@pytest.fixture
def dirwithfiles(tmpworkdir):
  img = PIL.Image.new('RGB', (100, 100))
  draw = ImageDraw.Draw(img)
  draw.text((10, 10), "img", fill=(255, 0, 0))
  del draw
  exifdata= piexif.dump({"0th":{},
                  "Exif":someexif,
                  "GPS":{},
                  "Interop":{},
                  "1st":{},
                  "thumbnail":None})
  img.save('img.jpg','jpeg',exif=exifdata)
  img.save('newimg.jpg','jpeg')
  with open('some.txt','w') as f: f.write('some.txt text here')
  os.mkdir('sub')
  [shutil.copy2(x,'sub') for x in glob('*.jpg')]
  return tmpworkdir

@pytest.fixture
def emptyhashfiles(dirwithfiles):
  ehf = ['.remdups_{}.sha256'.format(x) for x in Hasher.sources]
  for hf in ehf:
    with open(hf,'w'):pass
  return ehf

@pytest.fixture
def dups(emptyhashfiles):
  rd = Command()
  rd.hasher.hashall()
  with pytest.raises(AttributeError):
    rd.with_same_tail
  with pytest.raises(AttributeError):
    rd.no_same_tail
  for hf in emptyhashfiles:
    with open(hf,'r') as f:
      lns = f.readlines()
    assert len(lns)==5 #.remdups_* ignored
  return rd

@pytest.fixture
def othertmpdir(request):
  tempdir = tempfile.mkdtemp()
  request.addfinalizer(lambda :shutil.rmtree(tempdir))
  return tempdir

@pytest.yield_fixture
def here_otherdir(request,dirwithfiles,othertmpdir):
  os.chdir(othertmpdir)
  ehf = ['.remdups_{}.sha256'.format(x) for x in Hasher.sources]
  for hf in ehf:
    with open(hf,'w'):pass
  yield othertmpdir,dirwithfiles
  os.chdir(dirwithfiles)

##command line 

def test_help_global(capfd):
  with pytest.raises(SystemExit) as e:
    pa = parse_args(['remdups','-h'])
  out, err = capfd.readouterr()
  assert ','.join(['update','rm','mv','cp','dupsof','dupsoftail']) in out

@pytest.mark.parametrize('x',['update','rm','mv','cp','dupsof','dupsoftail'])
def test_help_command(capfd,x):
  with pytest.raises(SystemExit) as e:
    pa = parse_args(['remdups',x,'-h'])
  out, err = capfd.readouterr()
  assert "remdups "+x in out

def test_defaults_update(tmpworkdir):
   pa=parse_args(['remdups'])
   assert ('update', [], [], '.') == \
       (pa.cmd,pa.filter,pa.exclude,pa.fromdir)

@pytest.mark.parametrize('x',['rm','mv','cp'])
def test_defaults(tmpworkdir,x):
   pa=parse_args(['remdups',x,'-s','s.sh'])
   assert (x, 's.sh', [], [], [], False, False) == \
       (pa.cmd,pa.script.name,pa.comment_out,pa.keep_in,pa.keep_out,pa.only_same_name,pa.safe)
   assert os.path.exists('s.sh')
   del pa
   os.remove('s.sh')

@pytest.mark.parametrize('x',['dupsof','dupsoftail'])
def test_defaults_query(tmpworkdir,x):
   pa=parse_args(['remdups',x,'anystring'])
   assert (x, 'anystring') == (pa.cmd,pa.substr)

@pytest.mark.parametrize('a',['--keep-in','--keep-out','--comment-out'])#-i,-o,-c
def test_append(request,a):
   pa=parse_args(['remdups','cp','-s','s.sh',a, 'a',a, 'b'])
   assert vars(pa)[a.strip('-').replace('-','_')]==['a','b']
   del pa
   os.remove('s.sh')

@pytest.mark.parametrize('a',['--filter','--exclude'])#-f,-e
def test_append_update(request,a):
   pa=parse_args(['remdups','update',a, 'a',a, 'b'])
   assert vars(pa)[a.strip('-')]==['a','b']

##Hasher

def test_haslist_default(tmpworkdir):
  h=Hasher()
  assert h.hashfiles==['.remdups_c.sha256']

def test_haslist_more(tmpworkdir):
  lenah = len(Hasher.hashfilenames)
  for hf in Hasher.hashfilenames:
    with open(hf,'w'):pass
  assert len(os.listdir()) == lenah
  for hf in Hasher.hashfilenames:
    assert os.path.exists(hf)
  h=Hasher()
  h.load_hashes()
  h.hashall()
  for hf in Hasher.hashfilenames:
    with open(hf,'r') as f:
      lns = f.readlines()
    assert len(lns)==0 #.remdups_* ignored

def test_hash_and_write(emptyhashfiles,othertmpdir):
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
      try:
        os.makedirs(nfnd)
      except: pass
      assert content!=[] #because some .remdups_ with (c)ontent
      n = len(glob(nfnf+'*'))
      if n:
        nfnf = nfnf+'_'+str(n)
      with open(nfnf,'wb') as nf:
        for buf in content:
          nf.write(buf)
      same = filecmp.cmp(f, nfnf, False)
      assert same
  assert allduplicates==[hshr.relpath(x) for x in ['sub/img.jpg', 'sub/newimg.jpg']]
  hshr.clear()
  assert len(hshr.path_hash)==0
  allduplicates = []
  for f in hshr.scandir(fromdir=othertmpdir):
    if hshr.duplicates(f):
      allduplicates.append(f)
    with pytest.raises(ValueError):
      hshr.duplicates(f+'no')
  assert len(hshr.path_hash)==3
  assert allduplicates==[]
  #reload with no .remdups_c, but .remdups_e for non-exif files becomes _c
  for hf in glob('.remdups_*'):
    if '_c.' in hf:
      os.remove(hf)
  assert len(glob('.remdups_c.*'))==0
  hshr = Hasher()
  withcontent = 0
  for f,duplicates,content in hshr.foreachcontent('.'):
    withcontent += (content!=[])
  assert withcontent == 3
  #reload with no .remdups_c* and no .remdups_e*
  for hf in glob('.remdups_*'):
    if '_e.' in hf:
      os.remove(hf)
  assert len(glob('.remdups_e.*'))==0
  hshr = Hasher()
  for f,duplicates,content in hshr.foreachcontent('.'):
    assert content==[] #because no (c)ontent

def test_resort(emptyhashfiles,othertmpdir):
  resort(othertmpdir,"%y%m/%d_%H%M%S")
  hshr = Hasher()
  hshr.load_hashes()
  assert len(hshr.hash_paths)>0
  cd = os.getcwd()
  os.chdir(othertmpdir)
  hf = remdupsfile('e','md5')
  with open(hf,'w'): pass
  hshr = Hasher()
  assert len(glob(othertmpdir+'/**/*')) == 3
  assert len([f for f in hshr.scandir(othertmpdir,filter=['*.jpg'])]) == 1
  assert len([f for f in hshr.scandir(othertmpdir,filter=['*.no'])]) == 0
  os.chdir(cd)

def test_resort_no_content(emptyhashfiles,othertmpdir):
  for hf in glob('.remdups_*'):
    os.remove(hf)
  hf = remdupsfile('b','md5')
  with open(hf,'w'): pass
  with pytest.raises(ValueError):
    resort(othertmpdir,"%y%m/%d_%H%M%S")

##Command

@pytest.mark.parametrize('cmd,script',zip(['rm','cp','mv'],['script.sh','script.bat']))
def test_find_dups(dups,cmd,script):
  if cmd!='rm':
    with pytest.raises(ValueError):#see fn2dirfn
      cmds=getattr(dups,cmd)(script=argparse.FileType('w',encoding='utf-8')(script))
  cmds=getattr(dups,cmd)(script=argparse.FileType('w',encoding='utf-8')(script),sort="%y%m/%d%H%M%S")
  assert len(dups.with_same_tail)==2
  assert len(dups.no_same_tail)==0 #script.sh has no duplicate
  tails = [tail for tail, paths in dups.no_same_tail]
  assert not any(tails)
  assert len(dups.with_same_tail[0][1]) == 2
  assert len(cmds) == 14
  anybackslashes = any(['\\' in x for x in cmds])
  if script.endswith('.bat'):
    assert anybackslashes
  else:#.sh
    assert not anybackslashes
  if cmd=='rm':#remove all but one
    assert sum([re.match('^'+dups.comment+'>#',x) and 1 or 0 for x in cmds]) == 2
  else:#copy one and leave the rest
    assert sum([re.match('^'+dups.comment+'>#',x) and 1 or 0 for x in cmds]) == 2
  dups.args.script.close()
  assert os.path.exists(script)
  lns = []
  with open(script,'r') as f:
    lns = f.readlines()
  assert len(lns) == 14
          
@pytest.fixture
def updated(here_otherdir):
  here,other = here_otherdir
  main(parse_args(['remdups','update',str(other)]))
  for hf in glob('.remdups_*'):
    with open(hf,'r') as hfh:
      lns = hfh.readlines()
    assert len(lns)>0
    for e in lns:
      assert normp('//') in e
  return here_otherdir

def test_cp(updated):
  here,other = updated
  main(parse_args(['remdups','cp','-s','s.sh']))
  ld = os.listdir('.')
  assert 'img.jpg' in ld
  assert 'img.jpg' in ld
  assert 'sub' not in ld
          
##other
def test_convuinx(request):
  fn=r"U:\w&k(2)\wf g.txt"
  assert convunix(fn) == "'/U/w&k(2)/wf g.txt'"

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
