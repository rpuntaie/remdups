# -*- coding: utf-8 -*

'''

This tests remdups.py and makes 100% code coverage.

  $ py.test test_remdups.py --cov remdups.py --cov-report term-missing

'''

import os
import os.path
import tempfile
import subprocess
import shutil
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
  with open(hf,'r') as f:
    lns = f.readlines()
  assert len(lns)==lenah
  assert len(h.hash_paths)==lenah

@pytest.fixture
def img(tmpworkdir):
  img = PIL.Image.new('RGB', (1000, 1000))
  draw = ImageDraw.Draw(img)
  draw.text((10, 10), "img", fill=(255, 0, 0))
  del draw
  img.save('image.jpg','jpeg')
  return 'image.jpg'

def test_haslist_e(img):
  args=parse_args(['remdups','--script','s.sh','--hash-only'])
  hf = '.remdups_e.sha256'
  with open(hf,'w'):pass
  shutil.copy2(img,'new'+img)
  rd = RemDups(args)
  with open(hf,'r') as f:
    lns = f.readlines()
  assert len(lns)==4

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
