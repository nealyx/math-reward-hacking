"""Append-only record set: immutable per-key files, atomic commits, one writer."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import uuid


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def dump_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x") as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write("\n")
        f.flush();os.fsync(f.fileno())


def key(row):
    return row["model"],row["max_new_tokens"],row["problem_id"]


def filename(record_key):
    model,cap,example_id = record_key
    if model not in ("Base","robust_201","proxy_201","robust_202","proxy_202","robust_203","proxy_203"):
        raise ValueError("Unknown model")
    if cap not in (128,256,512) or type(example_id) is not int or not 0 <= example_id < 500:
        raise ValueError("Unknown cap or example")
    return f"{model}__{cap}__{example_id:04d}.jsonl"


def read_one(path):
    raw = Path(path).read_bytes()
    if not raw.endswith(b"\n") or len(raw.splitlines()) != 1:
        raise ValueError(f"Expected one complete JSONL row: {path}")
    row = json.loads(raw)
    if not isinstance(row,dict):raise ValueError(f"Nonobject row: {path}")
    return row


def read_committed(directory):
    records = {}
    for path in sorted(Path(directory).glob("*.jsonl")):
        row = read_one(path)
        record_key = key(row)
        if path.name != filename(record_key) or record_key in records:
            raise ValueError(f"Mismatched filename or duplicate: {path}")
        records[record_key] = row
    return records


def publish(directory, scratch, row):
    """Only a complete, fsynced new inode is linked into the canonical set.

    On interruption, pending scratch/raw journal bytes remain available. Existing
    canonical files are never opened for writing, renamed, truncated or replaced.
    """
    directory,scratch = Path(directory),Path(scratch)
    directory.mkdir(parents=True,exist_ok=True);scratch.mkdir(parents=True,exist_ok=True)
    destination = directory/filename(key(row))
    if destination.exists():
        if read_one(destination) != row:raise ValueError(f"Conflicting commit: {destination}")
        return False
    pending = scratch/(destination.name+"."+uuid.uuid4().hex+".pending")
    with pending.open("x") as f:
        f.write(json.dumps(row,allow_nan=False)+"\n");f.flush();os.fsync(f.fileno())
    try:
        os.link(pending,destination)
    except FileExistsError:
        if read_one(destination) != row:raise ValueError(f"Conflicting concurrent commit: {destination}")
        return False
    fd = os.open(directory,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return True


@contextmanager
def writer_lock(path):
    """Persistent inode; never unlink a lock another process may have opened."""
    with Path(path).open("a+") as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError("Another full-diagnostic writer is active")
        try:yield
        finally:fcntl.flock(handle,fcntl.LOCK_UN)
