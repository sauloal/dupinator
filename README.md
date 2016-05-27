dupinator
=========

The original dupinator.py script was created by Bill Bumgarner, and later improved by Andrew Shearer.

The "best" version will be simple called dupinator.py, the others are there for historical reference.

The script is used to find duplicate files, taking care to use as little CPU as possible, thus only comparing files of the same size, then checking the first kb for differences.

It also creates intermediate files permitting resuming the analysis in case of crash. The same mechanism allow the merging of different folders which allows parallelization of the analysis.


USAGE
=====
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
- Add proper comandline parameters
