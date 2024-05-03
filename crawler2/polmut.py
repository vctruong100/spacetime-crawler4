# crawler2/polmut.py
#
# thread-safe mutex that abides by the
# politeness timer

from threading import Lock, Timer


class PoliteMutex:
    """Mutex that abides by the politeness timer

    _mutex: Lock object
    _politeness: Politeness time delay
    """
    def __init__(self, politeness):
        self._politeness = politeness
        self._mutex = Lock()

    def lock(self):
        """Locks the mutex
        """
        self._mutex.acquire()

    __enter__ = lock

    def unlock(self):
        """Unlocks the mutex after waiting for the
        politeness timer delay
        """
        Timer(self._politeness, self._mutex.release).start()

    def __exit__(self, t, v, tb):
        self.unlock()

