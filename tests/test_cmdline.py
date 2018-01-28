
#requires: pytest-toolbox

import os
import mock
import pytest

import remdups
from remdups import *

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
