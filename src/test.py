import unittest

"""
This is the main test script. It discovers and runs all of the unit
tests. New tests can be put in the tests folder: just make sure the 
filename starts with "test".
"""

def main():
    loader = unittest.TestLoader()
    tests = loader.discover('../tests/')
    testRunner = unittest.runner.TextTestRunner()
    testRunner.run(tests)

if __name__ == '__main__':
    main()