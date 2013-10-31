
================================
remdups - remove duplicate files
================================

:Author: Roland Puntaier
:Homepage: https://github.com/rpuntaie/remdups
:License: See LICENSE file

remdups
=======

``remdups`` generates a script that removes duplicate files starting from file hashes.
It can also generate a these file hashes. It allows to specify which files to keep 
and which to remove. Byte-wise comparison available to be on the safe side.

The resulting script should be further inspected, possibly re-generated with different parameters
and finally executed separately in your shell.

Known Issues
============

Linux:
    None


Windows: 
    A gave it a try on Windows Cmd, but ran into problems due to 
    `Python Issue 1602 <http://bugs.python.org/issue1602>`_.
    So for file names with encodings falling into this issue it won't work.


Install
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

    $ py.test test_remdups.py --cov remdups.py --cov-report term-missing

  - consider sharing changes useful for others (github pull request).

Usage
=====

The intended procedure to remove duplicates with remdups is:

1. create file hash list:

   .. code-block:: console

     $ remdups --hash > hashes.txt

   or 

   .. code-block:: console

     $ find . -not -type d -exec sha256sum {} \; > hashes.txt

2. make a script with remove commands

   .. code-block:: console
     
     $ remdups [options] hashes.txt nodupes.sh

3. inspect the script and go back to 2., if necessary, else 4.

4. execute script

     $ nodupes.sh

5. remove empty directories:

   .. code-block:: console

     $ find . -empty -type d -delete


All in One
----------

This takes long, because all the hashes are create anew.
It is therefore not suitable to iterate with new parameters.

.. code-block:: console
    
  $ remdups


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

      $ find . -path "old" -prune -or -not -type d -and -iname "\*.jpg" -exec remdups --exif --hash {} \;


Generate the remove script
--------------------------

You start with the file hash list
  
.. code-block:: console

  $ remdups [options] hashes.txt > rm.sh

or 

.. code-block:: console

  $ remdups [options] hashes.txt rm.sh


At this stage you would use 

- ``-i`` and ``-o`` to choose which files get removed
- ``-c`` to comment out the remove command
- ``-r`` and ``-d`` to specify alternative remove commands for file and directory
- ``-x`` to specify the extension used for html files subdirectory.
  It defaults to ``_files``. If it starts with hyphen like ``-Dateien`` do ``-x="-Dateien"``.
- ``-n`` ``--only-same-name`` to ignore duplicates with different name
- ``-s`` ``--safe`` to do a final bytewise compare to make sure that files are really the same.
  You should add this option for the final remove script version. It can take a long time.
  After that you possibly still do manual changes to the script and then you execute it.

Help
====

Check out:

  $ remdups --help

For use from within python check out the code.

Similar tools
=============

I had to clean a sprawling directory and used python,
then decided to make a little command line tool out of it. 

Although I did a little googling before, 
only afterwards I found other links with similar tools.
I did not test them because my directory is deduped by now. 

I have made a Wikipedia page listing similar tools: 
`List of Duplicate File Finders <https://en.wikipedia.org/wiki/List_of_duplicate_file_finders>`_

