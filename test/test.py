#!/usr/bin/python

import unittest
import os
import sys
import shutil
import glob

sys.path.insert(0, '../')



def fun(x):
    return x + 1


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        self.folders = ['1', '2', '3', '4', '5', '6']
        
        self.randoms = [
            ('1/1.dat'    , 1024*1),
            ('2/2.dat'    , 1024*2),
            ('5/test.sync', 1024*3),
            ('5/test.log' , 1024*4),
            ('5/Thumbs.db', 1024*5)
        ]
        
        self.copies  = [
            ('1/1.dat', '3/1.dat' ),
            ('1/1.dat', '4/11.dat'),
        ]
        
        self.empties = [
            '6/empty.file'
        ]
        
        print
        print "creating test folders"
        for folder in self.folders:
            if os.path.exists(folder):
                print "folder exists"
                self.assertEqual(True, False)
            else:
                os.makedirs(folder)

        print "creating random files"
        for rid, (rnd, size) in enumerate(self.randoms):
            with open(rnd, 'w') as fhd:
                fhd.write("{}".format(rid)*size)
                
        print "creating copies"
        for src, dst in self.copies:
            shutil.copyfile(src, dst)

        print "creating empty files"
        for emp in self.empties:
            with open(emp, 'w') as fhd:
                fhd.write("")

    def tearDown(self):
        for folder in self.folders:
            shutil.rmtree(folder)
            
        for csv in glob.glob("*csv"):
            os.remove(csv)
            

    def test_forbidden(self):
        import dupinator as dp1
        class args: pass
        
        
        args.requireEqualNames = dp1.REQUIREEQUALNAMES
        args.verbose = True
        args.minSize = dp1.MINSIZE
        args.firstScanBytes = dp1.FIRSTSCANBYTES
        args.forbidden = dp1.FORBIDDEN
        args.ignore = dp1.IGNORE
        args.containing = dp1.CONTAINING
        args.output = None

        args.folders = self.folders

        
        filesBySize = dp1.run(args)
        
        print filesBySize
        
        self.assertEqual("a", "a")


    def atest_ignore(self):
        import dupinator as dp2
        self.assertEqual("a", "a")
        pass


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

