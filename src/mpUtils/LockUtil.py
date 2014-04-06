#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import time
import multiprocessing
GCHILD_RLOCK = multiprocessing.RLock()

def locker(func):
    def __anon(*args, **kwargs):
        # If already held, don't block/wait until lock is released
        # by current holder Just go to the else-clause and the
        # appropriate action will follow
        if GCHILD_RLOCK.acquire(False):
            print('\033[47mAcquired lock', func, '\033[00m')
            results = dict()
            try:
                results['data'] = func(*args, **kwargs)
            except Exception as ex:
                results['error'] = ex
            finally:
                # Release the lock
                print('\033[46mReleasedlock', func, '\033[00m')
                GCHILD_RLOCK.release()
            return results
        else:
            print('\033[41mCould not acquire lock. Try again\033[00m', func)
            return dict(
                needsRetry=True,
                error='Could not acquire lock. Try again later'
            )

    return __anon

def retryable(func, timeout=0.2):
    def __functor(*args, **kwargs):
        results = func(*args, **kwargs)
        if results and hasattr(results, 'get'):
            data = results.get('data', None)
            if data:
                print('Successful response from ', func, data)
                return data
            elif results.get('needsRetry', False):
                print('\033[33mRetrying after', timeout, ' secs\033[00m')
                time.sleep(timeout)
                return __functor(*args, **kwargs)
        else:
            msg = "Couldn't retry as 'get' method undefined for data"
            return dict(results=results, msg=msg)

    return __functor
