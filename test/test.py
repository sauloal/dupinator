#!/usr/bin/python

import unittest
import os
import sys
import shutil
import glob
import json

sys.path.insert(0, '../')

DEBUG = True


def compDbDicsOneWay(db1, db2, name=""):
    if name != "": name = " :: {} ::".format(name)

    #{"1024": {"ceecdf518271bb68bdcab5986abe4502": {"1.dat": ["1/1.dat", "8/1.dat"], "11.dat": ["8/11.dat"]}}, "2048": {"3ad57f7a6e7970075aae8d8a977abf25": {"2.dat": ["5/2.dat"], "22.dat": ["5/22.dat"]}, "5cf9ca0e398051164d9184921c8c1af2": {"3.dat": ["7/3.dat", "8/3.dat"], "2.dat": ["6/2.dat"], "22.dat": ["6/22.dat"]}, "444b71ef1e050ecabcfcfe62af97b7ab": {"2.dat": ["4/2.dat"], "22.dat": ["4/22.dat"]}}}
    for fileSize1, hashValues1 in sorted(db1.items()):
        if DEBUG: print "compDbDicsOneWay{} fileSize {}".format( name, fileSize1 )

        if fileSize1 not in db2:
            print "compDbDicsOneWay{} fileSize {} not found in: {}".format( name, fileSize1, ", ".join(sorted(db2.keys())))
            print "compDbDicsOneWay{} NOT OK".format( name )
            return False

        hashValues2 = db2[fileSize1]

        for hashValue1, baseNames1 in sorted(hashValues1.items()):
            if DEBUG: print "compDbDicsOneWay{}  hashValue {}".format( name, hashValue1 )

            if hashValue1 not in hashValues2:
                print "compDbDicsOneWay{} hashValue {} not found in: {}".format( name, hashValue1, ", ".join(sorted(hashValues2.keys())))
                print "compDbDicsOneWay{} NOT OK".format( name )
                return False

            baseNames2 = hashValues2[hashValue1]

            for baseName1, fileNames1 in sorted(baseNames1.items()):
                if DEBUG: print "compDbDicsOneWay{}   baseName {}".format( name, baseName1 )

                if baseName1 not in baseNames2:
                    print "compDbDicsOneWay{} baseName {} not found in: {}".format( name, baseName1, ", ".join(sorted(baseNames2.keys())))
                    print "compDbDicsOneWay{} NOT OK".format( name )
                    return False

                fileNames2 = baseNames2[baseName1]

                for fileName1 in sorted(fileNames1):
                    if DEBUG: print "compDbDicsOneWay{}    fileName {}".format( name, fileName1 )

                    if fileName1 not in fileNames2:
                        print "compDbDicsOneWay{} fileName {} not found in: {}".format( name, fileName1, ", ".join(sorted(fileNames2)))
                        print "compDbDicsOneWay{} NOT OK".format( name )
                        return False

    if DEBUG: print "compDbDicsOneWay  OK"
    return True


def compDbDicsTwoWays(db1, db2):
    res1 = compDbDicsOneWay(db1, db2, name="1x2")
    res2 = compDbDicsOneWay(db2, db1, name="2x1")
    res  = res1 and res2
    if DEBUG: print "compDbDicsTwoWays 1x2", ("OK" if res1 else "NOT OK")
    if DEBUG: print "compDbDicsTwoWays 2x1", ("OK" if res2 else "NOT OK")
    if DEBUG: print "compDbDicsTwoWays res", ("OK" if res  else "NOT OK")
    return res


class TestDupinatorOuputs(unittest.TestCase):
    def setUp(self):
        self.randoms = [
            ('1/1.dat'    , 1024*1, ('1')),
            ('1/1/1.dat'  , 1024*1, ('1')),
            ('1/1/1/1.dat', 1024*1, ('1')),
            ('2/2.dat'    , 1024*2, ('2')),
            ('3/test.sync', 1024*3, ('3')),
            ('3/test.log' , 1024*4, ('4')),
            ('3/Thumbs.db', 1024*5, ('5')),
            ('4/2.dat'    , 1024*2, ("2", "3")),
            ('4/22.dat'   , 1024*2, ("2", "3")),
            ('4/22.not'   , 1024*2, ("2", "3")),
            ('5/2.dat'    , 1024*2, ("2", "3", "4")),
            ('5/22.dat'   , 1024*2, ("2", "3", "4")),
            ('6/2.dat'    , 1024*2, ("2", "3", "4", "5")),
            ('6/22.dat'   , 1024*2, ("2", "3", "4", "5")),
            ('7/3.dat'    , 1024*2, ("2", "3", "4", "5")),
            ('8/3.dat'    , 1024*2, ("2", "3", "4", "5"))
        ]

        self.copies  = [
            ('1/1.dat', '8/1.dat' ),
            ('1/1.dat', '8/11.dat'),
        ]

        self.empties = [
            ('9/empty.file',)
        ]

        self.folders = []

        for db, cellPos in ((self.randoms, 0), (self.empties, 0), (self.copies, 1)):
            for fd in db:
                dirName = os.path.dirname(fd[cellPos])
                print fd[cellPos], ">", dirName
                self.folders.append(dirName)

        self.folders = sorted(list(set(self.folders)))

        print "folders", self.folders

        self.tearDown()

        print
        print "creating test folders"
        for folder in self.folders:
            if os.path.exists(folder):
                print "folder exists"
                assert False
            else:
                os.makedirs(folder)

        print "creating random files"
        for rid, (rnd, size, vals) in enumerate(self.randoms):
            with open(rnd, 'w') as fhd:
                text = ""

                for val in vals:
                    text += "{}".format(val)*(size/len(vals))

                while len(text) < size: text += "{}".format(vals[-1])
                print rid+1, rnd, size, vals#, text
                fhd.write(text)

        print "creating copies"
        for src, dst in self.copies:
            print " {} > {}".format(src, dst)
            shutil.copyfile(src, dst)

        print "creating empty files"
        for empG in self.empties:
            emp = empG[0]
            print " {}".format(emp)
            with open(emp, 'w') as fhd:
                fhd.write("")

    def tearDown(self):
        for folder in self.folders:
            if os.path.exists(folder):
                shutil.rmtree(folder)

        for csv in glob.glob("*csv"):
            os.remove(csv)

    def test_forbidden(self):
        import dupinator as dp1

        args = [
            "--verbose",
            "--debug",
            "--no_save",
            "--first_scan_bytes",
            "1024",
            "--forbidden",
            "22.dat"
        ] + self.folders

        filesBySize1 = dp1.run(args)

        jFilesBySize1 = json.dumps(filesBySize1)

        if DEBUG: print "\nfilesBySize1", filesBySize1 , "\n"
        if DEBUG: print "jFilesBySize1" , jFilesBySize1, "\n\n"

        expectedDict1 = {1024: {"ceecdf518271bb68bdcab5986abe4502": {"1.dat": ["1/1.dat", "1/1/1.dat", "1/1/1/1.dat", "8/1.dat"], "11.dat": ["8/11.dat"]}}, 2048: {"5cf9ca0e398051164d9184921c8c1af2": {"2.dat": ["6/2.dat"], "3.dat": ["7/3.dat", "8/3.dat"]}, "444b71ef1e050ecabcfcfe62af97b7ab": {"2.dat": ["4/2.dat"], "22.not": ["4/22.not"]}}}

        self.assertTrue(compDbDicsTwoWays(filesBySize1, expectedDict1))

        del dp1
        del filesBySize1
        del expectedDict1

    def test_ignore(self):
        import dupinator as dp2

        args = [
            "--verbose",
            "--debug",
            "--no_save",
            "--first_scan_bytes",
            "1024",
            "--ignore",
            ".not"
        ] + self.folders

        filesBySize2 = dp2.run(args)

        jFilesBySize2 = json.dumps(filesBySize2)

        #if DEBUG: print "\nfilesBySize", filesBySize , "\n"
        if DEBUG: print "\njFilesBySize" , jFilesBySize2, "\n\n"

        expectedDict2 = {1024: {"ceecdf518271bb68bdcab5986abe4502": {"1.dat": ["1/1.dat", "8/1.dat"], "11.dat": ["8/11.dat"]}}, 2048: {"5cf9ca0e398051164d9184921c8c1af2": {"2.dat": ["6/2.dat"], "3.dat": ["7/3.dat", "8/3.dat"]}, "444b71ef1e050ecabcfcfe62af97b7ab": {"2.dat": ["4/2.dat"]}}}

        self.assertTrue(compDbDicsTwoWays(filesBySize2, expectedDict2))

        del dp2
        del filesBySize2
        del expectedDict2

    def atest_contains(self):
        import dupinator as dp3
        self.assertEqual("a", "a")
        pass

    def atest_equal_names(self):
        import dupinator as dp4
        self.assertEqual("a", "a")
        pass



if __name__ == '__main__':
    unittest.main(verbosity=2)

