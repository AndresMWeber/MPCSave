#!/usr/bin/env python
"""
    :module: test_view
    :platform: None
    :synopsis: This module tests the view.py module
    :plans:
"""
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 1.0
#mpcSave_contextManager
import unittest
#from save import view

class TestModel(unittest.TestCase):
    def setUp(self):
        self.fixtures=[]
        pass

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture
    
    def test_view(self):
        self.assertEqual(1,1)

if __name__ == '__main__':
    unittest.main()
