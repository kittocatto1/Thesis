"""Download one large file over several parallel byte ranges.

Generic on purpose: this module knows nothing about GEO or any dataset, so it
can be reused for any big file on a server that supports range requests.
Standard library only.
"""

import os
import shutil
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BLOCK = 1 << 20  # copy 1 MiB at a time


def file_size(path):
    """Size of a file, or 0 if it does not exist."""
    return os.path.getsize(path) if os.path.exists(path) else 0


def remote_size(url):
    """Total size of the remote file, from a HEAD request."""
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=60) as response:
        return int(response.headers["Content-Length"])


def chunk_bounds(total, n):
    """Split [0, total) into at most n (index, start, end) ranges, end inclusive."""
    step = -(-total // n)  # ceiling division
    return [(i, start, min(start + step - 1, total - 1))
            for i, start in enumerate(range(0, total, step))]


def download_chunk(url, path, start, end, retries=3):
    """Fetch bytes [start, end] into path.

    A chunk that is already the right size is left alone, so rerunning after an
    interrupted download only fetches what is missing.
    """
    expected = end - start + 1
    if file_size(path) == expected:
        return expected

    headers = {"Range": f"bytes={start}-{end}"}
    for _ in range(retries):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=120) as response:
                with open(path, "wb") as handle:
                    shutil.copyfileobj(response, handle, BLOCK)
        except OSError:
            continue
        if file_size(path) == expected:
            return expected
    raise RuntimeError(f"chunk {start}-{end} failed after {retries} attempts")


def join_parts(paths, out_path):
    """Concatenate part files into one file."""
    with open(out_path, "wb") as out:
        for path in paths:
            with open(path, "rb") as handle:
                shutil.copyfileobj(handle, out, BLOCK)


def download(url, out_path, workers=12, total=None):
    """Download url to out_path using `workers` parallel ranges."""
    total = total or remote_size(url)
    if file_size(out_path) == total:
        print(f"already downloaded: {out_path}")
        return out_path

    parts_dir = out_path + ".parts"
    os.makedirs(parts_dir, exist_ok=True)
    bounds = chunk_bounds(total, workers)
    paths = [os.path.join(parts_dir, f"part.{i:03d}") for i, _, _ in bounds]
    print(f"{total / 1e9:.2f} GB in {len(bounds)} chunks -> {out_path}")

    finished = 0
    with ThreadPoolExecutor(max_workers=len(bounds)) as pool:
        jobs = [pool.submit(download_chunk, url, path, start, end)
                for (_, start, end), path in zip(bounds, paths)]
        for job in as_completed(jobs):
            job.result()  # re-raises whatever the worker hit
            finished += 1
            print(f"  chunk {finished}/{len(bounds)} done", flush=True)

    join_parts(paths, out_path)
    shutil.rmtree(parts_dir, ignore_errors=True)
    print(f"done: {out_path}")
    return out_path
