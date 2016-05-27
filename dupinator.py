#!/usr/bin/python

# Dupinator
# Original script by Bill Bumgarner: see
# http://www.pycs.net/bbum/2004/12/29/
#
# Updated by Andrew Shearer on 2004-12-31: see
# http://www.shearersoftware.com/personal/weblog/2005/01/14/dupinator-ii

import os
import sys
import stat
import md5
import pipes
from collections import defaultdict

filesBySize = defaultdict(list)
requireEqualNames = False
MINSIZE = 100
FIRST_SCAN_BYTES = 4096# 1024
FORBIDDEN = [ 'Thumbs.db', '.DS_Store' ]
dirsRead = 0
filesRead = 0

def walker(arg, dirname, fnames):
    d = os.getcwd()
    os.chdir(dirname)

    global filesBySize
    global dirsRead
    global filesRead

    dirsRead += 1

    dn = dirname
    if len(dirname) > 62:
        dn = dirname[:30]+'..'+dirname[-30:]

    print "dir {:<62s} - {:10,d} dirs {:10,d} files".format(dn, dirsRead, filesRead)

    sys.stdout.flush()

    fnames = [ f for f in fnames if f not in FORBIDDEN ]

    for f in fnames:
        filesRead += 1

        if filesRead % 10000 == 0:
            print "read {} files".format( filesRead )
            sys.stdout.flush()
        
        if not (os.path.isfile(f) or os.path.islink(f)):
            continue

        try:
            size = os.path.getsize(f)
        except:
            continue

        if size < MINSIZE:
            continue

        filesBySize[size].append(os.path.join(dirname, f))

    os.chdir(d)


def fmt3(num):
    for x in ['','Kb','Mb','Gb','Tb']:
        if num<1024:
            return "%3.1f%s" % (num, x)
        num /=1024



def main():
    if len(sys.argv) == 1:
        print "not path given"
        sys.exit(1)


    infiles = sys.argv[1:]
    outdb   = "_".join(infiles).replace("/","_").replace(" ","_")
    outdbFs = outdb + ".1.filesBySize.csv"
    outdbHa = outdb + ".2.hashes.csv"
    outdbDu = outdb + ".3.dupes.csv"
    outdbRm = outdb + ".4.rm.csv"
    outdbLn = outdb + ".5.ln.csv"

    print "Saving to {}".format(outdb)
    sys.stdout.flush()
    
    #quit()

    global filesBySize

    if os.path.exists(outdbFs):
        if os.path.exists(outdbHa) or os.path.exists(outdbDu):
            pass
        
        else:
            print "reading filesBySize db {}".format(outdbFs)
            sys.stdout.flush()
            
            with open(outdbFs) as fhd:
                for line in fhd:
                    line = line.strip()
                    
                    if len(line) == 0:
                        continue

                    cols = line.split("\t")
                    fileSize = int(cols[0])
                    filenames = cols[1:]
                    
                    filesBySize[fileSize] = filenames
                
    else:
        print "scannig filesystem"
        sys.stdout.flush()
        
        for x in infiles:
            print 'Scanning directory "{}"....'.format( x )
            os.path.walk(x, walker, filesBySize)

        #print filesBySize
        print "saving filesBySize db to {}".format(outdbFs)
        sys.stdout.flush()
        with open(outdbFs, "w") as fhd:
            for fileSize, filenames in filesBySize.items():
                fhd.write("{}\t{}\n".format(fileSize, "\t".join(filenames)))








    dupesCount = 0

    if os.path.exists(outdbHa):
        if os.path.exists(outdbDu):
            pass

        else:
            print "reading hashes db {}".format(outdbHa)
            sys.stdout.flush()

            filesBySize = defaultdict(lambda: defaultdict(list)) 

            with open(outdbHa) as fhd:
                for line in fhd:
                    line = line.strip()
                    
                    if len(line) == 0:
                        continue

                    cols = line.split("\t")
                    filesize, hashValue = cols[:2]
                    filegroup = cols[2:]
                    filesize = int(filesize)
                    
                    filesBySize[filesize][hashValue] = filegroup
    
    else:
        print "creathing hashes database"
        sys.stdout.flush()

        for k in sorted(filesBySize.keys()):
            inFiles = filesBySize[k]
            hashes = defaultdict(list)

            if len(inFiles) is 1:
                del filesBySize[k]
                continue

            print 'Testing {} files of size {}...'.format(len(inFiles), k)
            sys.stdout.flush()


            for fileName in inFiles:
                with file(fileName, 'r') as aFile:
                    hashValue = None
                    if k <= FIRST_SCAN_BYTES:
                        hasher = md5.new()

                        while True:
                            r = aFile.read(4096)

                            if not len(r):
                                break

                            hasher.update(r)
                            
                        hashValue = hasher.hexdigest()
                        
                    else:
                        hashValue = md5.new(aFile.read(FIRST_SCAN_BYTES)).hexdigest()
                    
                    hashes[hashValue].append(fileName)  # ashearer

            filesBySize[k] = hashes


        print "saving hashes db to {}".format(outdbHa)
        sys.stdout.flush()
        with open(outdbHa, "w") as fhd:
            for filesize, hashes in sorted(filesBySize.items()):
                for hashValue, fileGroup in sorted(hashes.items()):
                    fhd.write("{}\t{}\t{}\n".format(filesize, hashValue, "\t".join(sorted(fileGroup))))










    if os.path.exists(outdbDu):
        print "reading dups db {}".format(outdbDu)
        sys.stdout.flush()

        filesBySize = defaultdict(lambda: defaultdict(list)) 

        with open(outdbDu) as fhd:
            for line in fhd:
                line = line.strip()
                
                if len(line) == 0:
                    continue

                cols = line.split("\t")
                filesize, hashValue = cols[:2]
                filegroup = cols[2:]
                filesize = int(filesize)
                
                filesBySize[filesize][hashValue] = filegroup

    else:
        print "creating dups database"
        sys.stdout.flush()

        for k in filesBySize.keys():
            hashes = filesBySize[k]
            
            for hashValue in hashes.keys():
                fileGroup = hashes[hashValue]

                if len(fileGroup) == 1:
                    del hashes[hashValue]
                    continue


                if requireEqualNames:
                    if len(list(set([os.path.basename(f) for f in fileGroup]))) != 1:
                        del hashes[hashValue]
                        continue
                
            if len(hashes) == 0:
                del filesBySize[k]

        print "saving dupes db to {}".format(outdbDu)
        sys.stdout.flush()

        with open(outdbDu, "w") as fhd:
            for filesize, hashes in sorted(filesBySize.items()):
                for hashValue, fileGroup in sorted(hashes.items()):
                    fhd.write("{}\t{}\t{}\n".format(filesize, hashValue, "\t".join(sorted(fileGroup))))







    print "creating mitigation scripts"
    sys.stdout.flush()

    sourceCounter = 0
    fileCounter = 0
    bytesSaved = 0
    
    fhd_rm = open(outdbRm, "w")
    fhd_ln = open(outdbLn, "w")

    for filesize, hashes in sorted(filesBySize.items()):
        for hashValue, fileGroup in sorted(hashes.items()):
            sourceCounter += 1
            # Sort on length, as usually less interesting duplicates have longer names
            fileGroup.sort( lambda x,y: cmp(len(x), len(y)) )
            
            orig = fileGroup[0]
            origSize = os.path.getsize(orig)
            numCopies = len(fileGroup)-1
            #print 'Original {} is {} and has {} copies'.format(orig, fmt3(origSize), numCopies),
            
            bytesSavedHere = 0
            for f in fileGroup[1:]:
                fileCounter += 1
                fhd_rm.write('rm {}\n'.format(pipes.quote(f)))
                fhd_ln.write('rm {1} && ln {0} {1}\n'.format(pipes.quote(orig), pipes.quote(f)))
            
            bytesSavedHere  = origSize * numCopies
            bytesSaved     += bytesSavedHere
            
            #print 'saving {} (#{})\n'.format(fmt3(bytesSavedHere), sourceCounter)
            sys.stdout.flush()

    fhd_rm.close()
    fhd_ln.close()

    print "Will have saved {}; {} original file(s) duplicated in {} file(s).".format(fmt3(bytesSaved), fileCounter, sourceCounter)
    sys.stdout.flush()
    
if __name__ == "__main__":
    main()

