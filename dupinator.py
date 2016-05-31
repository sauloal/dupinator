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


#self.forbidden = [ 'Thumbs.db', '.DS_Store' ]

#walk.filesBySize[size][os.path.basename(f)].append(os.path.join(dirName, f))




def fmt3(num):
    for x in ['','Kb','Mb','Gb','Tb']:
        if num<1024:
            return "%3.1f%s" % (num, x)
        num /=1024


class walker(object):
    def __init__(self,
                 colNumber = 2,
                 containing = [],
                 forbidden = [],
                 ignore = [],
                 minSize = 100,
                 verbose = False,
                 debug = False
                 ):

        self.filesBySize = None

        self.containing = containing
        self.forbidden = forbidden
        self.ignore = ignore
        self.minSize = minSize
        self.verbose = verbose
        self.debug = debug

        self.dirsRead = 0
        self.filesRead = 0
        self.validFilesRead = 0

        self.initDb(colNumber)

        if self.debug: print "walker :: colNumber {} containing {} forbidden {} ignore {} minSize {} verbose {} debug {}".format(
            colNumber, containing,
            forbidden, ignore,
            minSize, verbose, debug )

    def initDb(self, colNumber):
        if   colNumber == 2:
            self.filesBySize = defaultdict(lambda: defaultdict(list))

        elif colNumber == 3:
            self.filesBySize = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        else:
            print " numcols {} should either be 2 or 3".format(colNumber)
            raise IndexError

    def walk(self, folder):
        os.path.walk(folder, self.walker, None)

    def walker(self, arg, dirName, fnames):
        self.dirsRead += 1

        if len(fnames) == 0:
            return

        d = os.getcwd()

        if self.debug: print "walker :: arg {} dirName {} files {} cwd {}".format( arg, dirName, len(fnames), d )

        os.chdir(dirName)

        numValidFiles = 0

        for f in xrange(len(fnames)-1, -1, -1):
            fname = fnames[f]


            self.filesRead += 1


            if self.filesRead % 10000 == 0:
                print "walker :: read {} files".format( self.filesRead )
                sys.stdout.flush()


            if len(self.forbidden) != 0:
                if fname in self.forbidden:
                    if self.debug: print "walker :: deleting {} for being forbidden".format(fname)
                    fnames.remove(fname)
                    continue

            if len(self.ignore) != 0:
                if any([fname.endswith(i) for i in self.ignore]):
                    if self.debug: print "walker :: deleting {} for ignoring one of {}".format(fname, ", ".join(self.containing))
                    fnames.remove(fname)
                    continue

            fullPath = os.path.join(dirName, fname)

            if len(self.containing) != 0:
                if any([c in fullPath for c in self.containing]):
                    if self.debug: print "walker :: deleting {} for containing one of {}".format(fullPath, ", ".join(self.containing))
                    fnames.remove(fname)
                    continue

            if not (os.path.isfile(fname) or os.path.islink(fname)):
                if self.verbose: print "walker :: {} not a file".format(fname)
                fnames.remove(fname)
                continue


            try:
                fileSize = os.path.getsize(fname)

            except:
                print "walker :: error getting size"
                raise SystemError


            if fileSize < self.minSize:
                if self.verbose: print "walker :: file {} too small ({} < {})".format(fname, fileSize, self.minSize)
                fnames.remove(fname)
                continue


            if self.debug: print "walker :: file {} {} fileSize {} #{}".format(fname, fullPath, fileSize, self.filesRead)

            numValidFiles += 1

            self.filesBySize[fileSize][fname].append(fullPath)


        self.validFilesRead += numValidFiles

        dn = self.shortenPath(dirName)

        if self.verbose: print ("walker :: dir {} - {:10,d} dirs {:10,d} files {:10,d} valid {:10,d} new\n").format(dn, self.dirsRead, self.filesRead, self.validFilesRead, numValidFiles)
        sys.stdout.flush()

        os.chdir(d)

    def shortenPath(self, dirName, dl=24):
        dp = (dl-2)/2
        dn = dirName

        if len(dn) > dl:
            dn = dn[:dp]+'..'+dn[-dp:]

        return ("{:<"+str(dl)+"s}").format(dn)

    def _check_num_cols(self):
        firstLevel = self.filesBySize[self.filesBySize.keys()[0]]
        secondLevel = firstLevel[firstLevel.keys()[0]]

        if isinstance(secondLevel, list):
            return 2

        else:
            return 3

    def iterDb(self):
        numCols = self._check_num_cols()

        if numCols == 2:
            for fileSize, baseNames in sorted(self.filesBySize.items()):
                for baseName, fileNames in sorted(baseNames.items()):
                    yield [str(fileSize), baseName]+fileNames
        else:
            for fileSize, hashValues in sorted(self.filesBySize.items()):
                for hashValue, baseNames in sorted(hashValues.items()):
                    for baseName, fileNames in sorted(baseNames.items()):
                        yield [str(fileSize), hashValue, baseName]+fileNames

    def readDb(self, inFile):
        numCols = self._check_num_cols()

        self.initDb(numCols)

        with open(inFile) as fhd:
            for line in fhd:
                line = line.strip()

                if len(line) == 0:
                    continue

                cols = line.split("\t")
                fileSize = int(cols[0])

                if numCols == 2:
                    baseName = cols[1]
                    fileNames = cols[2:]

                    self.filesBySize[fileSize][baseName] = fileNames

                else:
                    hashValue, baseName = cols[1:3]
                    fileNames = cols[3:]

                    self.filesBySize[fileSize][hashValue][baseName] = fileNames

    def saveDb(self, outFile, numCols):
        with open(outFile, "w") as fhd:
            for row in self.iterDb():
                fhd.write("\t".join(row) + "\n")

    def printDb(self):
        for row in self.iterDb():
            print "printing", " ".join(row)


def process(args):
    containing = args.containing
    debug = args.debug
    firstScanBytes = args.firstScanBytes
    forbidden = args.forbidden
    ignore = args.ignore
    infiles = args.folders
    minSize = args.minSize
    output = args.output
    requireEqualNames = args.requireEqualNames
    verbose = args.verbose
    saveToFile = args.saveToFile

    if debug:
        verbose = True

    if debug: print "ARGS", args

    walk = walker(
                    containing = containing,
                    debug = debug,
                    forbidden = forbidden,
                    ignore = ignore,
                    minSize = minSize,
                    verbose = verbose
                 )


    if len(infiles) == 0:
        print "no folder given"
        parser.print_help()
        sys.exit(1)

    infiles = sorted(list(set(infiles)))

    outdb = "_".join(infiles).replace("/","_").replace(" ","_")

    if output is not None:
        outdb = output

    outdbFs = outdb + ".1.filesBySize.csv"
    outdbHa = outdb + ".2.hashes.csv"
    outdbDu = outdb + ".3.dupes.csv"
    outdbRm = outdb + ".4.rm.csv"
    outdbLn = outdb + ".5.ln.csv"

    if saveToFile:
        print "Saving to {}".format(outdb)
        sys.stdout.flush()

    #quit()











    if saveToFile and os.path.exists(outdbFs):
        if os.path.exists(outdbHa) or os.path.exists(outdbDu):
            pass

        else:
            print "reading filesBySize db {}".format(outdbFs)
            sys.stdout.flush()

            walk.readDb(outdbFs)

    else:
        print "scannig filesystem"
        sys.stdout.flush()

        for x in infiles:
            print 'Scanning directory "{}"....'.format( x )
            walk.walk(x)

        print "read {} sizes, {} folders and {} files from which {} were valid".format(len(walk.filesBySize), walk.dirsRead, walk.filesRead, walk.validFilesRead)


        for fileSize, baseNames in sorted(walk.filesBySize.items()):
            for baseName, fileNames in sorted(baseNames.items()):
                baseNames[baseName] = sorted(list(set(fileNames)))


        if saveToFile:
            #print filesBySize
            print "saving filesBySize db to {}".format(outdbFs)
            sys.stdout.flush()

            walk.saveDb(outdbFs)

        if debug and not saveToFile:
            walk.printDb()









    if saveToFile and os.path.exists(outdbHa):
        if os.path.exists(outdbDu):
            pass

        else:
            print "reading hashes db {}".format(outdbHa)
            sys.stdout.flush()

            walk.readDb(outdbHa)

    else:
        print "creating hashes database"
        sys.stdout.flush()

        for fileSize, baseNames in sorted(walk.filesBySize.items()):
            allFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames]

            if debug: print "hashes :: size {} allFiles {}".format(fileSize, allFiles)

            if len(allFiles) <= 1:
                if verbose: print "hashes :: size {} had only one file {}".format(fileSize, allFiles[0])
                del walk.filesBySize[fileSize]
                continue


            if requireEqualNames:
                for baseName, fileNames in sorted(baseNames.items()):    
                    if len(fileNames) == 1:
                        if verbose: print "hashes :: size {} basename {} had only one file {}".format(fileSize, baseName, fileNames[0])
                        del walk.filesBySize[fileSize][baseName]

                allFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames]


                if len(allFiles) <= 1:
                    if verbose: print "hashes :: size {} had only one file {}".format(fileSize, allFiles[0])
                    del walk.filesBySize[fileSize]
                    continue





            hashValues = defaultdict(lambda: defaultdict(list))
            for fileName in allFiles:
                with file(fileName, 'r') as aFile:
                    hashValue = md5.new(aFile.read(firstScanBytes)).hexdigest()
                    baseName = os.path.basename(fileName)
                    hashValues[hashValue][baseName].append(fileName)  # ashearer

                    if debug: print "hashes :: size {} fileName {} baseName {} hashValue {}".format(fileSize, fileName, baseName, hashValue)




            for hashValue, baseNames in sorted(hashValues.items()):
                allHashFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames]

                if debug: print "hashes :: size {} hashValue {} allHashFiles {}".format(fileSize, hashValue, allHashFiles)

                if len(allHashFiles) <= 1:
                    if verbose: print "hashes :: size {} hash {} had only one file {}".format(fileSize, hashValue, allHashFiles[0])
                    del hashValues[hashValue]
                    continue

                if requireEqualNames:
                    for baseName, fileNames in sorted(baseNames.items()):
                        if len(fileNames) <= 1:
                            if verbose: print "hashes :: size {} hash {} had only one file {}".format(fileSize, hashValue, fileNames[0])
                            del hashValues[hashValue][baseName]

                    allHashFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames ]

                    if len(allHashFiles) <= 1:
                        if verbose: print "hashes :: size {} hash {} had only one file {}".format(fileSize, hashValue, allHashFiles[0])
                        del hashValues[hashValue]
                        continue



            if len(hashValues) == 0:
                if verbose: print "hashes :: size {} had no hash".format(fileSize)
                del walk.filesBySize[fileSize]
                continue


            walk.filesBySize[fileSize] = hashValues



        if saveToFile:
            print "saving hashes db to {}".format(outdbHa)
            sys.stdout.flush()
            walk.saveDb(outdbHa)

        if debug and not saveToFile:
            walk.printDb()











    if saveToFile and os.path.exists(outdbDu):
        print "reading dups db {}".format(outdbDu)
        sys.stdout.flush()

        walk.readDb(outdbDu)

    else:
        print "creating dups database"
        sys.stdout.flush()

        for fileSize, hashValues in sorted(walk.filesBySize.items()):
            print 'Testing {} hashes of size {}...'.format(len(hashValues), fileSize)
            sys.stdout.flush()

            nHashValues = defaultdict(lambda: defaultdict(list))

            for hashValue, baseNames in sorted(hashValues.items()):
                for baseName, fileNames in sorted(baseNames.items()):
                    for fileName in sorted(fileNames):
                        with file(fileName, 'r') as aFile:
                            hasher = md5.new()

                            for chunk in iter(lambda: aFile.read(4096), b""):
                                hasher.update(chunk)

                            nHashValue = hasher.hexdigest()
                            nHashValues[nHashValue][baseName].append(fileName)  # ashearer
                            if debug: print "dups :: size {} hashValue {} baseName {} fileName {} > new hash {}".format(fileSize, hashValue, baseName, fileName, nHashValue)


            for nHashValue, baseNames in sorted(nHashValues.items()):
                allFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames]

                if len(allFiles) <= 1:
                    if verbose: print "dups :: size {} hash {} had only one file {}".format(fileSize, nHashValue, allFiles[0])
                    del nHashValues[nHashValue]
                    continue


                if requireEqualNames:
                    for baseName, fileNames in sorted(baseNames.items()):    
                        if len(fileNames) == 1:
                            if verbose: print "dups :: size {} hash {} baseName {} had only one file {}".format(fileSize, nHashValue, baseName, fileNames[0])
                            del nHashValues[nHashValue][baseName]
                            continue

                    baseNames = nHashValues[nHashValue]

                    allFiles = [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames]


                    if len(allFiles) <= 1:
                        if verbose: print "dups :: size {} hash {} had only one file {}".format(fileSize, nHashValue, allFiles[0])
                        del nHashValues[nHashValue]
                        continue



            if len(nHashValues) == 0:
                if verbose: print "dups :: size {} had no hashes".format(fileSize)
                del walk.filesBySize[fileSize]

            else:
                walk.filesBySize[fileSize] = nHashValues



        if saveToFile:
            print "saving dups db to {}".format(outdbDu)
            sys.stdout.flush()

            walk.saveDb(outdbDu)

        if debug and not saveToFile:
            walk.printDb()














    print "creating mitigation scripts"
    sys.stdout.flush()

    sourceCounter = 0
    fileCounter = 0
    bytesSaved = 0

    fhd_rm = open(outdbRm, "w")
    fhd_ln = open(outdbLn, "w")

    # print filesBySize
    for fileSize, hashValues in sorted(walk.filesBySize.items()):
        for hashValue, baseNames in sorted(hashValues.items()):

            allFiles = []

            if requireEqualNames:
                for baseName, fileNames in sorted(baseNames.items()):
                    allFiles.append(fileNames)

            else:
                allFiles.append( [fileName for (baseName, fileNames) in baseNames.items() for fileName in fileNames] )

            if debug: print "out :: ", fileSize, hashValue, allFiles


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

                if verbose: print "out :: size {} hash {} original {} copies {}".format(fileSize, hashValue, orig, numCopies)
                if debug: print " copies:", copies

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

    return walk.filesBySize


def run(cmdline):
    parser = argparse.ArgumentParser(description='Dupinator. Fast and efficient identification of duplicated files.')

    parser.add_argument('--equal'     , '--equal_names'      , dest="requireEqualNames", action='store_true'                        , help="Require files to have the same name")
    parser.add_argument('--verbose'   ,                        dest="verbose"          , action='store_true'                        , help="verbose output")
    parser.add_argument('--debug'     ,                        dest="debug"            , action='store_true'                        , help="debug output")
    parser.add_argument('--no_save'   ,                        dest="saveToFile"       , action='store_false'                       , help="Do not save intermediate files")

    parser.add_argument('--out'       , '--output'           , dest="output"           , type=str           , default=None          , help="Output file base name (defaults to the normalized, concatenates folder names)")
    parser.add_argument('--min'       , '--min_size'         , dest="minSize"          , type=int           , default=100           , help="Minimum file size ({} bytes)".format(100))
    parser.add_argument('--first'     , '--first_scan_bytes' , dest="firstScanBytes"   , type=int           , default=4096          , help="Bytes to be read from file for quick hashing ({} bytes)".format(4096))
    parser.add_argument('--forbidden' , '--forbidden_files'  , dest="forbidden"        , action='append'    , default=[]            , help="files to be ignored ({}). will replace default".format(",".join([])))
    parser.add_argument('--ignore'    , '--ignore_extension' , dest="ignore"           , action='append'    , default=[]            , help="extensions to be ignored ({}). will replace default".format(",".join([])))
    parser.add_argument('--containing', '--ignore_containing', dest="containing"       , action='append'    , default=[]            , help="ignore files containing text ({}). will replace default".format(",".join([])))


    parser.add_argument('folders', nargs=argparse.REMAINDER)

    args = parser.parse_args(cmdline)

    return process(args)


def main(cmdline):
    run(cmdline)


if __name__ == "__main__":
    main(sys.argv[1:])

