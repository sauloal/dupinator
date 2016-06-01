dupinator
=========

The original dupinator.py script was created by Bill Bumgarner, and later improved by Andrew Shearer.

The "best" version will be simple called dupinator.py, the others are there for historical reference.

The script is used to find duplicate files, taking care to use as little CPU as possible, thus only comparing files of the same size, then checking the first kb for differences.

It also creates intermediate files permitting resuming the analysis in case of crash. The same mechanism allow the merging of different folders which allows parallelization of the analysis.


USAGE
=====

```bash
./dupinator.py -h
usage: dupinator.py [-h] [--equal] [--verbose] [--debug] [--no_save]
                    [--out OUTPUT] [--min MINSIZE] [--first FIRSTSCANBYTES]
                    [--forbidden FORBIDDEN] [--ignore IGNORE]
                    [--containing CONTAINING]
                    ...

Dupinator. Fast and efficient identification of duplicated files.

positional arguments:
  folders

optional arguments:
  -h, --help            show this help message and exit
  --equal, --equal_names
                        Require files to have the same name
  --verbose             verbose output
  --debug               debug output
  --no_save             Do not save intermediate files
  --out OUTPUT, --output OUTPUT
                        Output file base name (defaults to the normalized,
                        concatenates folder names)
  --min MINSIZE, --min_size MINSIZE
                        Minimum file size (100 bytes)
  --first FIRSTSCANBYTES, --first_scan_bytes FIRSTSCANBYTES
                        Bytes to be read from file for quick hashing (4096
                        bytes)
  --forbidden FORBIDDEN, --forbidden_files FORBIDDEN
                        files to be ignored (). will replace default
  --ignore IGNORE, --ignore_extension IGNORE
                        extensions to be ignored (). will replace default
  --containing CONTAINING, --ignore_containing CONTAINING
                        ignore files containing text (). will replace default
```

Example
=======

```bash
dupinator.py Backup Documents
```

OR

```bash
dupinator.py Backup
dupinator.py Documents

touch Backup_Documents.1.filesBySize.csv
cat Backup.2.hashes.csv Documents.2.hashes.csv > Backup_Documents.2.hashes.csv

dupinator.py Backup Documents
```

TODO
====
- Create better rules to find "original", as shortest isn't always the best guess.
