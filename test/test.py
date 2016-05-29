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
        self.folders = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        
        self.randoms = [
            ('1/1.dat'    , 1024*1, ('1')),
            ('2/2.dat'    , 1024*2, ('2')),
            ('3/test.sync', 1024*3, ('3')),
            ('3/test.log' , 1024*4, ('4')),
            ('3/Thumbs.db', 1024*5, ('5')),
            ('4/2.dat'    , 1024*2, ("2", "3")),
            ('4/22.dat'   , 1024*2, ("2", "3")),
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
            '9/empty.file'
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
        for rid, (rnd, size, vals) in enumerate(self.randoms):
            with open(rnd, 'w') as fhd:
                text = ""
                for val in vals:
                    text += "{}".format(val)*(size/len(vals))
                while len(text) < size: text += "{}".format(vals[-1])
                print rid, rnd, size, vals#, text
                fhd.write(text)
                
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

        args = [
            "--verbose",
            "--debug",
            "--no_save",
            "--first_scan_bytes",
            "1024"
        ] + self.folders
        
        filesBySize = dp1.run(args)
        
        print "filesBySize", filesBySize
        
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

