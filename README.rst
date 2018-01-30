================================
remdups - remove duplicate files
================================

:Author: Roland Puntaier
:Homepage: https://github.com/rpuntaie/remdups
:License: See LICENSE file

remdups
=======

``remdups`` generates a script to

- remove duplicate files

- copy files from another directory to this one, ignoring duplicates

- move files from another directory to this one, ignoring duplicates
  
The resulting script should be further inspected before executing it in your shell.

Usage
=====

0) Optional. You can choose one or more source+hashing methods, via e.g.::

      cat > .remdups_c.sha512
      cat > .remdups_e.md5

   All of .remdups_{c,b,d,e,n}.{sha512, sha384, sha256, sha224, sha1, md5} 
   contribute to the final hash. If you don't make such a file, the default is::

     .remdups_c.sha256

   {'c': 'content', 'b': 'block', 'd': 'date', 'e': 'exif', 'n': 'name'}

1. Create the hash file by either of (can take a long time)::

     remdups
     remdups update
     remdups update <fromdir>

   The hashes are added to all .remdups_x.y. To rehash all files::

     rm .remdups_*

2. Make a script with rm, mv, cp commands.
   It can be repeated with different options until the script is good.

   $remdups rm -s script.sh
   $remdups cp -s script.bat #if you used <fromdir>
   $remdups mv -s script.py  #if you used <fromdir>

   If the file ends in .sh, cp is used and the file names are in linux format.
   This is usable also on Windows with MSYS, MSYS2 and CYGWIN.

   If the file ends in .bat, Windows commands are used.

   If the file ends in .py, python functions are used.

3. Inspect the script and go back to 2., if necessary.
   Changes to the script can also be done with the editor.

4. execute script

   $./script.sh


Alternatively you can use remdups from your own python script, or interactively from a python prompt.

Install
=======


- Directly from PyPi:

.. code:: console

  $ pip install remdups


- From `github`_: Clone, change to the directory and do

.. code:: console

  $ python setup.py install

- If you plan to extend this tool

  - fork on `github`_
  - clone from your fork to you PC
  - do an editable install

  .. code:: console

    $ pip install -e .

  - test after change and bring coverage to 100%

  .. code:: console

    $ py.test --cov remdups.py --cov-report term-missing

  - consider sharing changes useful for others (`github`_ pull request).

.. hint:: 

    For more advanced file selection ``find`` can be used.
    The following example ignores directory ``old`` and produces a hash for all JPEG files:

    .. code:: console

       $ find . -path "old" -prune -or -not -type d -and -iname "\*.jpg" -exec sha256sum {} \; > .remdups_c.sha256

Command Line
============

The following is in addition to the help given with::

  remdups --help

The sources for the hashes can be::

   {'c': 'content', 'b': 'block', 'd': 'date', 'e': 'exif', 'n': 'name'}

Don't include ``n``, because same files with different names cannot be found. ``c`` is the best.

Do e.g::

      cat > .remdups_b.sha512
      cat > .remdups_c.sha256

Fill the hash files from the current directory::

  remdups update

Or fill the hash files from another directory::

  remdups update <fromdir>

In the latter case the paths in the hash files will have a ``//`` or ``\\``
to mark the start for the new relatives paths in a subsequent ``mv`` or ``cp`` command.

Once the hash files are filled create the script. It depend on the extension used::

  remdups <command> -s script.sh <options>
  remdups <command> -s script.bat <options>
  remdups <command> -s script.py <options>

``command`` can be ``rm``, ``cp``, ``mv``.
There is also ``dupsof`` and ``dupsoftail``, but they don't take a ``--script``, but print the output.

``--keep-in``, ``--keep-out`` and ``--comment-out`` will remove different files of a duplicate group.
``--safe`` will do a byte-wise comparison, before creating the script. That takes longer.

``cp`` and ``mv`` also take ``--sort``: In this case the tree is not recreated, but the files are sorted
to the provided tree structure using the file modification date. See https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior.

API
===

With your own python script you can load the file for hashing and use the
loaded content immediately to create the new file, if not duplicate.

.. code:: python

  from remdups import *
  hasher = Hasher()
  allduplicates = []
  for filename,duplicates,content in hasher.foreachcontent('.'):
    if duplicates:
      allduplicates.append(f)
    else:
      assert content!=[] #some .remdups_ must be with (c)ontent
      with open('afilehere','wb') as nf:
        for buf in content:
          nf.write(buf)

``foreachcontent()`` uses ``scandir()``, but does not add duplicate files to the ``.remdup_`` files.

.. code:: python

   for f in hasher.scandir(otherdir,filter=['*.jpg'],exclude=['**/old/*']):
      duplicates = hasher.duplicates(f)
      yield (f,duplicates,kw['content'])
      if duplicates:
         hasher.clear(f)
      else:
         hasher.update_hashfiles()

If you don't want to keep the content, don't provide a ``[]`` for ``content`` in ``scandir``.
``scandir()`` will hash all files not yet in the ``.remdup_`` files and will return the file name.

This code resorts a tree by hashing and creating a copy, if not duplicate.

.. code:: python

   import os
   import remdups
   os.chdir('dir/to/resort/to')
   with open('.remdups_c.sha256','w'): pass
   remdups.resort('../some/dir/here',"%y%m/%d_%H%M%S")


.. _`github`: https://github.com/rpuntaie/remdups
