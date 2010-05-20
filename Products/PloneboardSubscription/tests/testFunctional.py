"""PloneboardSubscription functional doctests.  This module collects all *.txt
files in the tests directory and runs them. (stolen from Ploneboard)
"""

import os, sys

import glob
import doctest
import unittest
from Globals import package_home
from Testing.ZopeTestCase import FunctionalDocFileSuite as Suite

from Products.PloneboardSubscription.config import GLOBALS

# Load products
from Products.PloneboardSubscription.tests.PloneboardSubscriptionTC import FunctionalTestCase

OPTIONFLAGS = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)

test_files_in_order = [ 'MemberSubscribesToForum.txt',
                        'MemberSubscribesToConv.txt',
                        'CheckMailTemplate.txt',
                      ]

def list_doctests():
    home = package_home(GLOBALS)
    filenames = [os.path.sep.join([home, 'tests', filename]) for filename in test_files_in_order]
    return filenames

def test_suite():

    filenames = list_doctests()

    return unittest.TestSuite(
        [Suite(os.path.basename(filename),
               optionflags=OPTIONFLAGS,
               package='Products.PloneboardSubscription.tests',
               test_class=FunctionalTestCase)
         for filename in filenames]
        )
