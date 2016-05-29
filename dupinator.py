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
DEBUG = False
MINSIZE = 100
FIRSTSCANBYTES = 4096# 1024
FORBIDDEN = [ 'Thumbs.db', '.DS_Store' ]
IGNORE = []
CONTAINING = []

DIRSREAD = 0
FILESREAD = 0
VALIDFILESREAD = 0

#filesBySize[size][os.path.basename(f)].append(os.path.join(dirname, f))
filesBySize = defaultdict(lambda: defaultdict(list))


def walker(arg, dirname, fnames):
    d = os.getcwd()
    os.chdir(dirname)

    global filesBySize
    global DIRSREAD
    global FILESREAD
    global VALIDFILESREAD

    DIRSREAD += 1

    dn = dirname
    if len(dirname) > 62:
        dn = dirname[:30]+'..'+dirname[-30:]

    print "dir {:<62s} - {:10,d} dirs {:10,d} files".format(dn, DIRSREAD, FILESREAD)

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
        FILESREAD += 1
        
        if FILESREAD % 10000 == 0:
            print "walker :: read {} files".format( FILESREAD )
            sys.stdout.flush()
        
        if not (os.path.isfile(f) or os.path.islink(f)):
            if VERBOSE: print "walker :: not a file"
            continue

        try:
            fileSize = os.path.getsize(f)
        except:
            print "walker :: error getting size"
            sys.exit(1)

        if VERBOSE: print "walker :: file {} fileSize {} #{}".format(f, fileSize, FILESREAD)

        if fileSize < MINSIZE:
            if VERBOSE: print "walker :: file {} too small ({} < {})".format(f, fileSize, MINSIZE)
            continue

        VALIDFILESREAD += 1

        filesBySize[fileSize][os.path.basename(f)].append(os.path.join(dirname, f))

    os.chdir(d)


def fmt3(num):
    for x in ['','Kb','Mb','Gb','Tb']:
        if num<1024:
            return "%3.1f%s" % (num, x)
        num /=1024



def main(cmdline):
    run(cmdline)
    
    
def run(cmdline):
    parser = argparse.ArgumentParser(description='Dupinator. Fast and efficient identification of duplicated files.')

    parser.add_argument('--equal'     , '--equal_names'      , dest="requireEqualNames", action='store_true'                        , help="Require files to have the same name")
    parser.add_argument('--verbose'   ,                        dest="verbose"          , action='store_true'                        , help="Verbose output")
    parser.add_argument('--debug'     ,                        dest="debug"            , action='store_true'                        , help="Debug output")
    parser.add_argument('--no_save'   ,                        dest="saveToFile"       , action='store_false'                       , help="Do not save intermediate files")
    
    parser.add_argument('--out'       , '--output'           , dest="output"           , type=str           , default=None          , help="Output file base name (defaults to the normalized, concatenates folder names)")
    parser.add_argument('--min'       , '--min_size'         , dest="minSize"          , type=int           , default=MINSIZE       , help="Minimum file size ({} bytes)".format(MINSIZE))
    parser.add_argument('--first'     , '--first_scan_bytes' , dest="firstScanBytes"   , type=int           , default=FIRSTSCANBYTES, help="Bytes to be read from file for quick hashing ({} bytes)".format(FIRSTSCANBYTES))
    parser.add_argument('--forbidden' , '--forbidden_files'  , dest="forbidden"        , action='append'    , default=FORBIDDEN     , help="files to be ignored ({}). will replace default".format(",".join(FORBIDDEN)))
    parser.add_argument('--ignore'    , '--ignore_extension' , dest="ignore"           , action='append'    , default=IGNORE        , help="extensions to be ignored ({}). will replace default".format(",".join(IGNORE)))
    parser.add_argument('--containing', '--ignore_containing', dest="containing"       , action='append'    , default=CONTAINING    , help="ignore files containing text ({}). will replace default".format(",".join(CONTAINING)))


    parser.add_argument('folders', nargs=argparse.REMAINDER)

    args = parser.parse_args(cmdline)
    
    return process(args)


def process(args):
    global REQUIREEQUALNAMES
    global VERBOSE
    global DEBUG
    global MINSIZE
    global FIRSTSCANBYTES
    global FORBIDDEN
    global IGNORE
    global CONTAINING

    global filesBySize


    REQUIREEQUALNAMES = args.requireEqualNames
    VERBOSE = args.verbose
    DEBUG = args.debug
    MINSIZE = args.minSize
    FIRSTSCANBYTES = args.firstScanBytes
    FORBIDDEN = args.forbidden
    IGNORE = args.ignore
    CONTAINING = args.containing
    
    if DEBUG:
        VERBOSE = True
        
    saveToFile = args.saveToFile

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

    if saveToFile:
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
                    baseName =     cols[1]
                    fileNames = cols[2:]
                    
                    filesBySize[fileSize][baseName] = fileNames

    else:
        print "scannig filesystem"
        sys.stdout.flush()
        
        for x in infiles:
            print 'Scanning directory "{}"....'.format( x )
            os.path.walk(x, walker, filesBySize)

        print "read {} sizes, {} folders and {} files from which {} were valid".format(len(filesBySize), DIRSREAD, FILESREAD, VALIDFILESREAD)

        if saveToFile:
            #print filesBySize
            print "saving filesBySize db to {}".format(outdbFs)
            sys.stdout.flush()
            
            with open(outdbFs, "w") as fhd:
                for fileSize, baseNames in sorted(filesBySize.items()):
                    for baseName, fileNames in sorted(baseNames.items()):
                        if DEBUG: print "saving files", fileSize, baseName, fileNames
                        fhd.write("\t".join([str(fileSize), baseName]+fileNames) + "\n")


        if DEBUG and not saveToFile:
            for fileSize, baseNames in sorted(filesBySize.items()):
                for baseName, fileNames in sorted(baseNames.items()):
                    print "saving files", fileSize, baseName, fileNames









    if os.path.exists(outdbHa):
        if os.path.exists(outdbPu) or os.path.exists(outdbDu):
            pass

        else:
            print "reading hashes db {}".format(outdbHa)
            sys.stdout.flush()

            filesBySize = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

            with open(outdbHa) as fhd:
                for line in fhd:
                    line = line.strip()
                    
                    if len(line) == 0:
                        continue

                    cols = line.split("\t")
                    fileSize, hashValue, baseName = cols[:3]
                    fileSize = int(fileSize)
                    fileNames = cols[3:]
                    
                    filesBySize[fileSize][hashValue][baseName] = fileNames
    
    else:
        print "creating hashes database"
        sys.stdout.flush()

        for fileSize, baseNames in sorted(filesBySize.items()):
            allFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames]

            if DEBUG: print "hashes :: size {} allFiles {}".format(fileSize, allFiles)

            if len(allFiles) <= 1:
                if VERBOSE: print "hashes :: size {} had only one file {}".format(fileSize, allFiles[0])
                del filesBySize[fileSize]
                continue

            
            if REQUIREEQUALNAMES:
                for baseName, fileNames in sorted(baseNames.items()):    
                    if len(fileNames) == 1:
                        if VERBOSE: print "hashes :: size {} basename {} had only one file {}".format(fileSize, baseName, fileNames[0])
                        del filesBySize[fileSize][baseName]
    
                allFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames]


                if len(allFiles) <= 1:
                    if VERBOSE: print "hashes :: size {} had only one file {}".format(fileSize, allFiles[0])
                    del filesBySize[fileSize]
                    continue





            hashes = defaultdict(lambda: defaultdict(list))
            for fileName in allFiles:
                with file(fileName, 'r') as aFile:
                    hashValue = md5.new(aFile.read(FIRSTSCANBYTES)).hexdigest()
                    baseName = os.path.basename(fileName)
                    hashes[hashValue][baseName].append(fileName)  # ashearer
    
                    if DEBUG: print "hashes :: size {} fileName {} baseName {} hashValue {}".format(fileSize, fileName, baseName, hashValue)
    


    
            for hashValue, baseNames in sorted(hashes.items()):
                allHashFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames]
                
                if DEBUG: print "hashes :: size {} hashValue {} allHashFiles {}".format(fileSize, hashValue, allHashFiles)
                
                if len(allHashFiles) <= 1:
                    if VERBOSE: print "hashes :: size {} hash {} had only one file {}".format(fileSize, hashValue, allHashFiles[0])
                    del hashes[hashValue]
                    continue
                
                if REQUIREEQUALNAMES:
                    for baseName, fileNames in sorted(baseNames.items()):
                        if len(fileNames) <= 1:
                            if VERBOSE: print "hashes :: size {} hash {} had only one file {}".format(fileSize, hashValue, fileNames[0])
                            del hashes[hashValue][baseName]

                    allHashFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames ]

                    if len(allHashFiles) <= 1:
                        if VERBOSE: print "hashes :: size {} hash {} had only one file {}".format(fileSize, hashValue, allHashFiles[0])
                        del hashes[hashValue]
                        continue



            if len(hashes) == 0:
                if VERBOSE: print "hashes :: size {} had no hash".format(fileSize)
                del filesBySize[fileSize]
                continue


            filesBySize[fileSize] = hashes



        if saveToFile:
            print "saving hashes db to {}".format(outdbHa)
            sys.stdout.flush()
            with open(outdbHa, "w") as fhd:
                for fileSize, hashes in sorted(filesBySize.items()):
                    for hashValue, baseNames in sorted(hashes.items()):
                        for baseName, fileNames in sorted(baseNames.items()):
                            if DEBUG: print "saving hashes", fileSize, hashValue, baseName, fileNames
                            fhd.write("\t".join([str(fileSize), hashValue, baseName]+fileNames) + "\n")

        if DEBUG and not saveToFile:
            for fileSize, hashes in sorted(filesBySize.items()):
                for hashValue, baseNames in sorted(hashes.items()):
                    for baseName, fileNames in sorted(baseNames.items()):
                        print "saving hashes", fileSize, hashValue, baseName, fileNames            











    if os.path.exists(outdbDu):
        print "reading dups db {}".format(outdbDu)
        sys.stdout.flush()

        filesBySize = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        with open(outdbDu) as fhd:
            for line in fhd:
                line = line.strip()
                
                if len(line) == 0:
                    continue

                cols = line.split("\t")
                fileSize, hashValue, baseName = cols[:3]
                fileSize = int(fileSize)
                fileNames = cols[3:]
                
                filesBySize[fileSize][hashValue][baseName] = fileNames
    
    else:
        print "creating dups database"
        sys.stdout.flush()

        for fileSize, hashes in sorted(filesBySize.items()):
            print 'Testing {} hashes of size {}...'.format(len(hashes), fileSize)
            sys.stdout.flush()

            nHashes = defaultdict(lambda: defaultdict(list))

            for hashValue, baseNames in sorted(hashes.items()):
                for baseName, fileNames in sorted(baseNames.items()):
                    for fileName in sorted(fileNames):
                        with file(fileName, 'r') as aFile:
                            hasher = md5.new()
    
                            for chunk in iter(lambda: aFile.read(4096), b""):
                                hasher.update(chunk)
                                                    
                            nHashValue = hasher.hexdigest()
                            nHashes[nHashValue][baseName].append(fileName)  # ashearer
                            if DEBUG: print "dups :: size {} hashValue {} baseName {} fileName {} > new hash {}".format(fileSize, hashValue, baseName, fileName, nHashValue)
            

            for nHashValue, baseNames in sorted(nHashes.items()):
                allFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames]

                if len(allFiles) <= 1:
                    if VERBOSE: print "dups :: size {} hash {} had only one file {}".format(fileSize, nHashValue, allFiles[0])
                    del nHashes[nHashValue]
                    continue
    
                
                if REQUIREEQUALNAMES:
                    for baseName, fileNames in sorted(baseNames.items()):    
                        if len(fileNames) == 1:
                            if VERBOSE: print "dups :: size {} hash {} baseName {} had only one file {}".format(fileSize, nHashValue, baseName, fileNames[0])
                            del nHashes[nHashValue][baseName]
                            continue
        
                    baseNames = nHashes[nHashValue]
        
                    allFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames]
    
    
                    if len(allFiles) <= 1:
                        if VERBOSE: print "dups :: size {} hash {} had only one file {}".format(fileSize, nHashValue, allFiles[0])
                        del nHashes[nHashValue]
                        continue

                

            if len(nHashes) == 0:
                if VERBOSE: print "dups :: size {} had no hashes".format(fileSize)
                del filesBySize[fileSize]
                
            else:
                filesBySize[fileSize] = nHashes



        if saveToFile:
            print "saving dups db to {}".format(outdbDu)
            sys.stdout.flush()
            with open(outdbDu, "w") as fhd:
                for fileSize, hashes in sorted(filesBySize.items()):
                    for hashValue, baseNames in sorted(hashes.items()):
                        for baseName, fileNames in sorted(baseNames.items()):
                            if DEBUG: print "saving dups", fileSize, hashValue, baseName, fileNames
                            fhd.write("\t".join([str(fileSize), hashValue, baseName] + fileNames) + "\n")

        if DEBUG and not saveToFile:
            for fileSize, hashes in sorted(filesBySize.items()):
                for hashValue, baseNames in sorted(hashes.items()):
                    for baseName, fileNames in sorted(baseNames.items()):
                        print "saving dups", fileSize, hashValue, baseName, fileNames














    print "creating mitigation scripts"
    sys.stdout.flush()

    sourceCounter = 0
    fileCounter = 0
    bytesSaved = 0
    
    fhd_rm = open(outdbRm, "w")
    fhd_ln = open(outdbLn, "w")

    # print filesBySize
    for fileSize, hashes in sorted(filesBySize.items()):
        for hashValue, baseNames in sorted(hashes.items()):
            
            allFiles = []
            
            if REQUIREEQUALNAMES:
                for baseName, fileNames in sorted(baseNames.items()):
                    allFiles.append(fileNames)
                    
            else:
                allFiles.append( [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames] )

            if DEBUG: print "out :: ", fileSize, hashValue, allFiles


            for fileGroup in allFiles:
                sourceCounter += 1
    
                #print fileGroup
    
                # Sort on length, as usually less interesting duplicates have longer names
                fileGroup.sort( lambda x,y: cmp(len(x), len(y)) )
                
                
                orig = fileGroup[0]
                copies = fileGroup[1:]
                origSize = os.path.getsize(orig)
                numCopies = len(copies)
                #print 'Original {} is {} and has {} copies'.format(orig, fmt3(origSize), numCopies),
                
                bytesSavedHere = 0
                    
                if VERBOSE: print "out :: size {} hash {} original {} copies {}".format(fileSize, hashValue, orig, numCopies)
                if DEBUG: print " copies:", copies

                for f in sorted(copies):
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
    
    return filesBySize



    
if __name__ == "__main__":
    main(sys.argv[1:])

