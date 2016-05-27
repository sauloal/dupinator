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
import argparse
from collections import defaultdict


REQUIREEQUALNAMES = False
VERBOSE = False
MINSIZE = 100
FIRSTSCANBYTES = 4096# 1024
FORBIDDEN = [ 'Thumbs.db', '.DS_Store' ]
IGNORE = []
CONTAINING = []

dirsRead = 0
filesRead = 0

filesBySize = defaultdict(list)


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


    if VERBOSE: print "walker :: files before           filtering {}".format(len(fnames))


    fnames = [ f for f in fnames if f not in FORBIDDEN ]
    if VERBOSE: print "walker :: files after forbidden  filtering {}".format(len(fnames))



    for f in xrange(len(fnames)-1, 0, -1):    
        if any([f.endswith(i) for i in IGNORE]):
            fnames.remove(f)
    if VERBOSE: print "walker :: files after ignore     filtering {}".format(len(fnames))
    

    
    for f in xrange(len(fnames)-1, 0, -1):    
        if any([(c in f) for c in CONTAINING]):
            fnames.remove(f)
    if VERBOSE: print "walker :: files after containing filtering {}".format(len(fnames))



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

        if VERBOSE: print "walker :: file {} size {} #{}".format(f, size, filesRead)

        if size < MINSIZE:
            if VERBOSE: print "walker :: file {} too small ({} < {})".format(f, size, MINSIZE)
            continue

        filesBySize[size].append(os.path.join(dirname, f))

    os.chdir(d)


def fmt3(num):
    for x in ['','Kb','Mb','Gb','Tb']:
        if num<1024:
            return "%3.1f%s" % (num, x)
        num /=1024



def main():
    parser = argparse.ArgumentParser(description='Dupinator. Fast and efficient identification of duplicated files.')

    parser.add_argument('--equal'     , '--equal_names'      , dest="requireEqualNames", action='store_true'                        , help="Require files to have the same name")
    parser.add_argument('--verbose'   ,                        dest="verbose"          , action='store_true'                        , help="Verbose output")
    
    parser.add_argument('--out'       , '--output'           , dest="output"           , type=str           , default=None          , help="Output file base name (defaults to the normalized, concatenates folder names)")
    parser.add_argument('--min'       , '--min_size'         , dest="minSize"          , type=int           , default=MINSIZE       , help="Minimum file size ({} bytes)".format(MINSIZE))
    parser.add_argument('--first'     , '--first_scan_bytes' , dest="firstScanBytes"   , type=int           , default=FIRSTSCANBYTES, help="Bytes to be read from file for quick hashing ({} bytes)".format(FIRSTSCANBYTES))
    parser.add_argument('--forbidden' , '--forbidden_files'  , dest="forbidden"        , action='append'    , default=FORBIDDEN     , help="files to be ignored ({}). will replace default".format(",".join(FORBIDDEN)))
    parser.add_argument('--ignore'    , '--ignore_extension' , dest="ignore"           , action='append'    , default=IGNORE        , help="extensions to be ignored ({}). will replace default".format(",".join(IGNORE)))
    parser.add_argument('--containing', '--ignore_containing', dest="containing"       , action='append'    , default=CONTAINING    , help="ignore files containing text ({}). will replace default".format(",".join(CONTAINING)))


    parser.add_argument('folders', nargs=argparse.REMAINDER)

    args = parser.parse_args()
    
    run(args)


def run(args):
    global REQUIREEQUALNAMES
    global VERBOSE
    global MINSIZE
    global FIRSTSCANBYTES
    global FORBIDDEN
    global IGNORE
    global CONTAINING

    global filesBySize


    REQUIREEQUALNAMES = args.requireEqualNames
    VERBOSE = args.verbose
    MINSIZE = args.minSize
    FIRSTSCANBYTES = args.firstScanBytes
    FORBIDDEN = args.forbidden
    IGNORE = args.ignore
    CONTAINING = args.containing

    infiles = args.folders

    if len(infiles) == 0:
        print "no folder given"
        parser.print_help()
        sys.exit(1)
    
    outdb   = "_".join(infiles).replace("/","_").replace(" ","_")
    
    if args.output is not None:
        outdb = args.output
    
    outdbFs = outdb + ".1.filesBySize.csv"
    outdbHa = outdb + ".2.hashes.csv"
    outdbPu = outdb + ".3.potential_dupes.csv"
    outdbDu = outdb + ".4.dupes.csv"
    outdbRm = outdb + ".5.rm.csv"
    outdbLn = outdb + ".6.ln.csv"

    print "Saving to {}".format(outdb)
    sys.stdout.flush()
    
    #quit()


    if os.path.exists(outdbFs):
        if os.path.exists(outdbHa) or os.path.exists(outdbPu) or os.path.exists(outdbDu):
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








    if os.path.exists(outdbHa):
        if os.path.exists(outdbPu) or os.path.exists(outdbDu):
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
        print "creating hashes database"
        sys.stdout.flush()

        for k in sorted(filesBySize.keys()):
            inFiles = filesBySize[k]
            hashes = defaultdict(list)

            if len(inFiles) == 1:
                if VERBOSE: print "hashes :: size {} had only one file {}".format(k, inFiles[0])
                del filesBySize[k]
                continue

            print 'Testing {} files of size {}...'.format(len(inFiles), k)
            sys.stdout.flush()


            for fileName in inFiles:
                with file(fileName, 'r') as aFile:
                    hashValue = md5.new(aFile.read(FIRSTSCANBYTES)).hexdigest()
                    hashes[hashValue].append(fileName)  # ashearer

            filesBySize[k] = hashes


        print "saving hashes db to {}".format(outdbHa)
        sys.stdout.flush()
        with open(outdbHa, "w") as fhd:
            for filesize, hashes in sorted(filesBySize.items()):
                for hashValue, fileGroup in sorted(hashes.items()):
                    fhd.write("{}\t{}\t{}\n".format(filesize, hashValue, "\t".join(sorted(fileGroup))))










    if os.path.exists(outdbPu):
        print "reading potential dups db {}".format(outdbPu)
        sys.stdout.flush()

        filesBySize = defaultdict(lambda: defaultdict(list)) 

        with open(outdbPu) as fhd:
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
        print "creating potential dups database"
        sys.stdout.flush()

        for k in sorted(filesBySize.keys()):
            hashes = filesBySize[k]
            
            for hashValue in sorted(hashes.keys()):
                fileGroup = hashes[hashValue]

                if len(fileGroup) == 1:
                    if VERBOSE: print "potential :: size {} hash {} had only one file {}".format(k, hashValue, fileGroup[0])
                    del filesBySize[k][hashValue]

                elif REQUIREEQUALNAMES:
                    #TODO: check if at least 2 share the same name not if all share it
                    fcounter = defaultdict(list)

                    for f in sorted(fileGroup):
                        fcounter[os.path.basename(f)].append(f)

                    if len(fcounter) != 1:
                        ivalidsBasenames = []
                        
                        for fGroupNum, (fBasename, files) in enumerate(sorted(fcounter.items())):
                            if len(files) == 1:
                                fileGroup.remove(files[0])
                                ivalidsBasenames.append(fBasename)
                            
                        for inv in ivalidsBasenames:
                            if VERBOSE: print "potential :: size {} hash {} basename {} has only one file".format(k, hashValue, inv)
                            del fcounter[inv]
                            
                        if   len(fcounter) == 0: # no names left. delete hash
                            if VERBOSE: print "potential :: size {} hash {} has no file".format(k, hashValue)
                            del filesBySize[k][hashValue]
                            
                        elif len(fcounter) == 1: # just one name. nothing to do
                            pass
                            
                        else: # more than one name, more than one file per name
                            for fGroupNum, (fBasename, fileNames) in enumerate(sorted(fcounter.items())):
                                if VERBOSE: print "potential :: size {} hash {} basename {} separated in {}".format(k, hashValue, fBasename, fGroupNum)
                                filesBySize[k]["{}-{}".format(hashValue,fGroupNum)] = fileNames
                            
                            del filesBySize[k][hashValue]
                            

                
            if len(filesBySize[k]) == 0:
                if VERBOSE: print "potential :: size {} hash {} has no file".format(k, hashValue)
                del filesBySize[k]

        print "saving potential dups db to {}".format(outdbDu)
        sys.stdout.flush()

        with open(outdbPu, "w") as fhd:
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

        for k in sorted(filesBySize.keys()):
            inFiles = filesBySize[k]
            hashes = defaultdict(lambda: defaultdict(list))

            print 'Testing {} files of size {}...'.format(len(inFiles), k)
            sys.stdout.flush()

            for fileName in inFiles:
                with file(fileName, 'r') as aFile:
                    hasher = md5.new()

                    for chunk in iter(lambda: aFile.read(4096), b""):
                        hasher.update(chunk)
                                            
                    hashValue = hasher.hexdigest()
                    hashes[hashValue][os.path.basename(fileName)].append(fileName)  # ashearer

                
            for hashValue, baseNames in sorted(hashes.values()):
                if REQUIREEQUALNAMES:
                    for basename, fileNames in sorted(baseNames.values()):
                        if len(fileNames) == 1:
                            if VERBOSE: print "dups :: size {} hash {} basename {} has only one file".format(k, hashValue, basename)
                            del hashes[hashValue][basename]
                    
                    baseNames = hashes[hashValue]
                    
                    if   len(baseNames) == 0:
                        if VERBOSE: print "dups :: size {} hash {} has no files".format(k, hashValue)
                        del hashes[hashValue]
                        
                    elif len(baseNames) == 1:
                        survivingBaseName = baseNames.keys()[0]
                        hashes[hashValue] = baseNames[survivingBaseName]
                        
                    else:
                        for fGroupNum, (basename, fileNames) in enumerate(sorted(baseNames.items())):
                            if VERBOSE: print "dups :: size {} hash {} basename {} separated in {}".format(k, hashValue, basename, fGroupNum)
                            hashes["{}-{}".format(hashValue,fGroupNum)] = fileNames
                            
                        del hashes[hashValue]
                        
                else:
                    hashes[hashValue] = [y for y in baseNames[x] for x in baseNames]

            filesBySize[k] = hashes


        print "saving dups db to {}".format(outdbDu)
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
            copies = fileGroup[1:]
            origSize = os.path.getsize(orig)
            numCopies = len(copies)
            #print 'Original {} is {} and has {} copies'.format(orig, fmt3(origSize), numCopies),
            
            bytesSavedHere = 0
            for f in sorted(copies):
                fileCounter += 1
                
                if VERBOSE: print "out :: size {} hash {} original {} copies {}".format(filesize, hashValue, orig, numCopies)
                
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
    
    return filesBySize



    
if __name__ == "__main__":
    main()

