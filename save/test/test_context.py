#!/usr/bin/env python
"""
    :module: test_context
    :platform: None
    :synopsis: This module tests the context.py module
    :plans:
"""
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 1.0
#mpcSave_contextManager
import unittest
#from save import context

class TestModel(unittest.TestCase):
    def setUp(self):
        self.fixtures=[]
        pass

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture
    
    def test_context(self):
        self.assertEqual(1,1)

if __name__ == '__main__':
    unittest.main()
