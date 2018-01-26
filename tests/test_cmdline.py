
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
  assert ','.join(['rm','mv','cp','dupsof','dupsoftail']) in out

@pytest.mark.parametrize('x',['rm','mv','cp','dupsof','dupsoftail'])
def test_help_command(capfd,x):
  with pytest.raises(SystemExit) as e:
    pa = parse_args(['remdups',x,'-h'])
  out, err = capfd.readouterr()
  assert "remdups "+x in out

def test_defaults(tmpworkdir):
   pa=parse_args(['remdups','-s','s.sh'])
   assert ('rm', 's.sh', [], [], [], [], False, False, False) == \
       (pa.cmd,pa.script.name,pa.comment_out,pa.keep_in,pa.keep_out,pa.exclude_dir,pa.hash_only,pa.only_same_name,pa.safe)
   assert os.path.exists('s.sh')

def test_append(request):
   pa=parse_args(['remdups','-s','s.sh','-i', 'a','-i', 'b'])
   assert pa.keep_in==['a','b']
