import unittest

import log
import logging

"""
This is the main test script. It discovers and runs all of the unit
tests. New tests can be put in the tests folder: just make sure the 
filename starts with "test".
"""

def main():
    log.initialize(console_level=log.NONE, filename="unittest") # Ensuring no logging is shown in the console
    logging.info("\n")
    logging.info("Starting unit tests.")

    loader = unittest.TestLoader()
    tests = loader.discover('tests/')
    testRunner = unittest.runner.TextTestRunner()
    testRunner.run(tests)

    logging.info("Finished unit tests.")

if __name__ == '__main__':
    main()