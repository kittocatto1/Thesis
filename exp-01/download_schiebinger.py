"""Download the Schiebinger 2019 reprogramming time course (GEO GSE122662).

    python download_schiebinger.py --dest /kaggle/working/data

or from a notebook:

    import sys; sys.path.insert(0, ".../experiment/exp-01")
    from download_schiebinger import fetch
    tar_path = fetch()
"""

import argparse
import os
import tarfile
import urllib.request

from parallel_download import download

BASE = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE122nnn/GSE122662/suppl"
TAR_URL = f"{BASE}/GSE122662_RAW.tar"
MANIFEST_URL = f"{BASE}/filelist.txt"
TAR_BYTES = 1865574400  # published size, so we can skip the HEAD request


def default_dest():
    """/kaggle/working/data on Kaggle, ./data anywhere else."""
    if os.path.isdir("/kaggle/working"):
        return "/kaggle/working/data"
    return os.path.join(os.getcwd(), "data")


def fetch_manifest(dest):
    """Grab filelist.txt (~16 KB): the per-sample inventory."""
    path = os.path.join(dest, "filelist.txt")
    urllib.request.urlretrieve(MANIFEST_URL, path)
    print(f"manifest: {path}")
    return path


def fetch(dest=None, workers=12):
    """Download the 1.7 GB archive. Returns the path to the tar."""
    dest = dest or default_dest()
    os.makedirs(dest, exist_ok=True)
    return download(TAR_URL, os.path.join(dest, "GSE122662_RAW.tar"),
                    workers=workers, total=TAR_BYTES)


def extract(tar_path, dest=None):
    """Unpack the archive into <dest>/GSE122662/. Needs ~1.7 GB more."""
    dest = dest or os.path.dirname(tar_path)
    out_dir = os.path.join(dest, "GSE122662")
    os.makedirs(out_dir, exist_ok=True)
    with tarfile.open(tar_path, "r:") as archive:
        archive.extractall(out_dir)
    print(f"extracted to {out_dir}")
    return out_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default=None, help="output directory")
    parser.add_argument("--workers", type=int, default=12,
                        help="parallel connections (default: 12)")
    parser.add_argument("--extract", action="store_true", help="unpack the tar")
    parser.add_argument("--manifest", action="store_true", help="also get filelist.txt")
    args = parser.parse_args()

    dest = args.dest or default_dest()
    os.makedirs(dest, exist_ok=True)
    if args.manifest:
        fetch_manifest(dest)
    tar_path = fetch(dest=dest, workers=args.workers)
    if args.extract:
        extract(tar_path, dest)


if __name__ == "__main__":
    main()
