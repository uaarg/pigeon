import unittest
import logging
import argparse
import sys

import log

"""
This is the main test script. It discovers and runs all of the unit
tests. New tests can be put in the tests folder: just make sure the
filename starts with "test".
"""

def main():
    ap = argparse.ArgumentParser(description="Run unit tests.")
    ap.add_argument("test_name", nargs="?", default=None, help="Run a specific module, test class, or test.")
    ap.add_argument("--verbose", "-v", action="count", default=1, help="Increase the amount of information printed to stdout.")
    args = ap.parse_args()

    log.initialize(console_level=log.NONE, filename="unittest") # Ensuring no logging is shown in the console
    logging.info("\n")
    logging.info("Starting unit tests.")

    unittest.installHandler()
    loader = unittest.TestLoader()
    if args.test_name:
        sys.path.insert(0, "tests")
        tests = loader.loadTestsFromName(args.test_name)
    else:
        tests = loader.discover('tests/')
    testRunner = unittest.runner.TextTestRunner(verbosity=args.verbose)
    testRunner.run(tests)

    logging.info("Finished unit tests.")

if __name__ == '__main__':
    main()