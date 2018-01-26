
#requires: pytest-toolbox

import os
import mock
import pytest

import remdups
from remdups import *

#def test_wd(tmpworkdir):
#  assert os.getcwd()==str(tmpworkdir)

def test_help(capfd):
  with pytest.raises(SystemExit) as e:
    parser = parse_args(['-h'])
  out, err = capfd.readouterr()
  assert "Create shell script to remove duplicates, for further inspection." in out

def test_no_script(request):
  with pytest.raises(SystemExit) as e:
    parser = parse_args([])

def test_defaults(request):
   pa=parse_args(['-s','s.sh'])
   assert ('rm', 's.sh', [], [], [], [], False, False, False) == \
       (pa.cmd,pa.script.name,pa.comment_out,pa.keep_in,pa.keep_out,pa.exclude_dir,pa.hash_only,pa.only_same_name,pa.safe)

def test_append(request):
   pa=parse_args(['-s s.sh','-i a','-i b'])
