"""One advisory native Civ V test lease per macOS user, across worktrees.

Every test runner must hold this lease from before preparation through restoration.
The kernel releases the lease on process exit. This does not replace checking for
an existing game process or recovering a runner's interrupted-session journal.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path

LOCK_PATH = Path('/private/tmp') / f'civ5-native-test-{os.getuid()}.lock'


@contextmanager
def native_test_lock(owner, evidence, path=LOCK_PATH):
    with path.open('a+') as lease:
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lease.seek(0)
            raise RuntimeError('Civ V native test lease is held: ' + lease.read()) from None
        try:
            lease.seek(0)
            lease.truncate()
            json.dump({'owner': owner, 'supervisor_pid': os.getpid(),
                       'evidence': str(Path(evidence).resolve())}, lease)
            lease.flush()
            yield
        finally:
            fcntl.flock(lease, fcntl.LOCK_UN)
