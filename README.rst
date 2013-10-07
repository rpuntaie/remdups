
================================
remdups - remove duplicate files
================================

:Author: Roland Puntaier
:Homepage: https://github.org/rpuntaie/remdups
:License: See LICENSE file

remdups
=======

- it generates a script that removes duplicate files starting from file hashes
- it can also generate a list of file hashes

The resulting script should be further inspected, possibly re-generated with different parameters
and finally executed separately from your shell.

install
=======

- Directly from PyPi:

.. code-block:: console

  $ pip install remdups


- From github: Clone, change to directory and do

.. code-block:: console

  $ python setup.py install

- If you plan to extend this tool

  - fork on github
  - clone locally from your fork
  - do an editable install

  .. code-block:: console

    $ pip install -e .

  - test after change and bring coverage to 100%

  .. code-block:: console

    $ py.test --cov-report  term-missing --cov remdups.py

  - consider sharing changes useful for others.
    (google github pull requests)

Use cases
=========

The intended procedure with remdups is:

1. create file hash list:

   .. code-block:: console

     $remdups --hash 

   or 

   .. code-block:: console

     $find . -not -type d -exec sha256sum {} \;

2. make a script with remove commands

3. inspect the script and go back to 2., if necessary, else 4.

4. execute script


All in One
----------

This takes long, because all the hashes are create anew.
It is therefore not suitable to iterate with new parameters.

.. code-block:: console
    
  $ remdups.py


File Hash List
--------------

The file hash list as an intermediate starting point makes it faster to iterate with new parameters.

There are more ways to generate the file hash list.

- Use find with a checksum generator
  

.. code-block:: console

  $ find . -not -type d -exec sha256sum {} \; > hashes.txt

- Use remdups

  ``remdups`` allows to make a file hash list with the ``--hash`` option and no input file.

  .. code-block:: console
  
    $ remdups --hash > hashes.txt 


With ``--hash`` one can use the ``--exclude-dir`` to ignore certain directories.

``--hash`` together with a file can replace system checksum tools.
``remdups`` has these source options: ``--name``, ``--namedate``, ``--exif``, ``--content``, ``--block``.
For full content ``md5sum`` or ``shaXsum`` (X=1, 224, 256, 384, 512) system tools are faster.

.. hint:: 

    For more advanced file selection ``find`` should be used.
    The following example ignores directory ``old`` and produces a hash for all JPEG files by their EXIF data.

    .. code-block:: console

      $ find . -path "old" -prune -or -not -type d -and -iname "\*.jpg" -exec remdups.py --exif --hash {} \;


Generate the remove script
--------------------------

You start with the file hash list
  
.. code-block:: console

  $ remdups [options] hashes.txt > rm.sh

or 

.. code-block:: console

  $ remdups [options] hashes.txt rm.sh


In this stage you would use 

- ``-i`` and ``-o`` to choose which files get removed
- ``-c`` to comment out the remove command
- ``-r`` and ``-d`` to specify alternative remove commands for file and directory
- ``-x`` to specify the extension used for html files subdirectory.
  It defaults to ``_files``. If it starts with hyphen like ``-Dateien`` do ``-x="-Dateien"``.
- ``-n`` ``--only-same-name`` to ignore duplicates with different name
- ``-s`` ``--safe`` to do a final bytewise compare to make sure that files are really the same
  You should add this option for the final remove script version. It can take a long time.
  After that you possibly still do manual changes to the script and then you execute it.


Help
----

Check out:

  $ remdups --help

And look into the code.


API
---

For use from within python check out the code.

