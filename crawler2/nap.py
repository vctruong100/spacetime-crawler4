# crawler2/nap.py
#
# thread-safe persistence
# represents a hash map of Nurls (node urls)
# with dicts and msgpack
#
# single operations on dicts are guaranteed thread-safe by Python

from threading import Event, RLock, Thread, main_thread
from utils import get_logger, get_urlhash, normalize
from crawler2.nurl import Nurl
import os
import msgpack


class _Nap_Autosave(Thread):
    """Auto-save thread for Naps (nurl maps).

    nap: Nap object
    sig: Event object
    alarm: Seconds until next wake-up
    threshold: Minimum write count to call nap.save()
    """
    def __init__(self, nap, alarm, threshold):
        self.nap = nap
        self.sig = Event()
        self.alarm = alarm
        self.threshold = threshold

        super().__init__()

    def run(self):
        nap = self.nap
        sig = self.sig
        alarm = self.alarm

        # Event.wait() allows thread to sleep
        # interruptible by its internal flag using Event.set()
        sig.wait(alarm)

        # thread continues to run iff
        # main thread is alive and signal is unset
        while not sig.is_set() and main_thread().is_alive():
            nap.logger.info("auto-save alarm")

            # locking isn't necessary when getting writecnt
            # thread eventually fetches the latest writecnt
            if nap.writecnt >= self.threshold:
                nap.logger.info("auto-save threshold met")
                nap.save()
            sig.wait(alarm)

        # if main thread died and Nap object is unclosed, save one last time
        if not main_thread().is_alive() and not nap.closed:
            nap.logger.info("attempting emergency save (main thread died)")
            nap.save()


class Nap:
    """Thread-safe persistent hash maps of Nurls (node urls).
    See crawler2/nurl.py for info on the Nurl class.

    To get and set nurls from naps, use it like a dict.
    Single operations are thread-safe, so you must use nap.mutex
    to encapsulate multiple operations as one transaction.
    ```
        with nap.mutex:
            nurl = nap[url]
            nurl.absdepth += 1
            nap[url] = nurl
    ```

    Note: Nurls are cached and immutable. Updating multiple attributes of the 
    same Nurl is treated as one thread-safe operation / transaction when you 
    write to a Nap object.

    closed      Whether Nap object was closed
    fname       Nap filename
    writecnt    Write count since last save
    autosave    Auto-save thread (defaults: 2 seconds, 20 min writes)
    logger      Logger object

    dict        Dictionary with actual data
    trans       Dictionary with incoming transactions (NOT IMPLEMENTED)
    mutex       Reentrant lock object on dict
    """
    def __init__(self, fname, autosave_interval=2, autosave_threshold=20):
        self.closed = False
        self.fname = fname
        self.writecnt = 0
        self.autosave = _Nap_Autosave(self, autosave_interval, autosave_threshold)
        self.logger = get_logger("nap")

        self.dict = None
        self.mutex = RLock()

        # open file if it exists
        if os.path.exists(fname):
            with open(fname, "rb") as fh:
                size = int.from_bytes(fh.read(4), "little")
                self.dict = msgpack.unpackb(fh.read(size), raw=False)

        # if dict is invalid, create empty dict
        if not self.dict or not isinstance(self.dict, dict):
            self.dict = dict()

        # log init message
        self.logger.info(
            f"init {fname}, "
            f"save={autosave_interval}, "
            f"threshold={autosave_threshold}"
        )

        # start autosave
        self.autosave.start()


    def __getitem__(self, url):
        """Magic method for retrieving a nurl from a URL string.
        Returns a root nurl of the URL if hash doesn't exist.
        The nurl returned is cached and does not update the actual data.

        :param url str: The URL string
        :return: A Nurl object that represents the URL string
        :rtype: Nurl
        """
        with self.mutex:
            _norm_url = normalize(url)
            _hash = get_urlhash(_norm_url)
            _dict = self.dict.get(_hash, None)
            _nurl = Nurl.from_dict(_dict) if _dict else Nurl(_norm_url)
            if not _dict:
                self.dict.__setitem__(_hash, _nurl.__dict__.copy())
            return _nurl


    def __setitem__(self, url, nurl):
        """Magic method for setting a nurl from a URL string.

        If you wish to set from get (cached nurl) in a thread-safe manner,
        enclose both operations with self.mutex.

        :param url str: The URL string
        :param nurl Nurl: The new Nurl object
        """
        with self.mutex:
            _hash = get_urlhash(normalize(url))
            self.dict.__setitem__(_hash, nurl.__dict__.copy())
            self.writecnt += 1


    def exists(self, url):
        """Checks if url exists as an entry in the Nap dict.

        :param url str:
        :return: Whether url exists
        :rtype: bool
        """
        with self.mutex:
            _norm_url = normalize(url)
            _hash = get_urlhash(_norm_url)
            return _hash in self.dict


    def close(self, max_retries=3):
        """Closes the Nap object.
        Stops autosaving and saves the final dict.
        If saving fails, retry up to `max_retries`.
        NOTE: The main thread SHOULD call this before exiting.

        :return: Whether final save succeeded
        :rtype: bool
        """
        self.logger.info("received close()")
        write_ok = False

        # stop autosaving
        self.autosave.sig.set()
        self.autosave.join()

        self.logger.info("joined autosave thread")

        # attempt to save once
        # if it fails, retry up to max_retries
        for i in range(max_retries+1):
            if self.save():
                write_ok = True
                break

        # log close message
        self.logger.info(f"successfully closed (final_save={write_ok})")

        self.closed = True # mark as closed
        return write_ok


    def save(self):
        """Tries saving contents to fname.
        If nothing was written from last save, then it aborts and succeeds.
        This function is thread-safe.

        For the sake of simplicity, saving locks all reads/writes.
        It's possible to implement a transaction system to allow
        reads and writes during saving. This would require a separate mutex
        for saving.

        :return: Whether save succeeded
        :rtype: bool
        """
        write_ok = False

        # saving should be atomic
        # lock access to data
        with self.mutex:
            # writes only if write_cnt > 0
            # abort save if unchanged (and save succeeds)
            if self.writecnt <= 0:
                return True

            # write to tmp file
            with open(f"{self.fname}.tmp", "wb") as fh:
                packed = msgpack.packb(self.dict, use_bin_type=True)
                fh.write(len(packed).to_bytes(4, "little"))
                fh.write(packed)
                self.writecnt = 0
                write_ok = True

        # if write OK, remove and rename
        if write_ok:
            if os.path.exists(self.fname):
                os.remove(self.fname)
            os.rename(f"{self.fname}.tmp", self.fname)
            self.logger.info(f"saved to {self.fname}")

        return write_ok

