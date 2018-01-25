
#requires: pytest-toolbox

import os
import mock

@mock.patch('remdups.rm','remdups.mv','remdups.cp')
def test_argparse(request):
  parser = parse_args(['-l', '-m'])
  self.assertTrue(parser.long)

def test_wd(tmpworkdir):
  assert os.getcwd()==str(tmpworkdir)
