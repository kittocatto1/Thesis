# exp-01 — Schiebinger 2019 (GSE122662) download

Fetches the raw 10x archive for the Waddington-OT reprogramming time course
(Schiebinger et al. 2019, *Cell* 176(4):928–943), GEO accession **GSE122662**.
`GSE122662_RAW.tar` is 1.7 GB: 216 files, 172 samples, 39 timepoints D0–D18.

## Two files

| File | Job |
|---|---|
| `parallel_download.py` | generic: download any big file over parallel byte ranges |
| `download_schiebinger.py` | GEO-specific: URLs, paths, unpacking |

`parallel_download.py` knows nothing about GEO, so you can reuse it for LARRY
or anything else.

## Why not just `wget`

NCBI throttles one connection to ~5–31 KB/s, which makes this a 16-hour
download. It does support range requests, so we pull 12 ranges at once. Chunks
that are already the right size are skipped, so an interrupted run resumes.

## On Kaggle

Enable **Settings → Internet** first.

```python
!git clone --depth 1 https://github.com/<you>/<repo>.git /kaggle/working/thesis

import sys
sys.path.insert(0, "/kaggle/working/thesis/experiment/exp-01")
from download_schiebinger import fetch

tar_path = fetch()          # -> /kaggle/working/data/GSE122662_RAW.tar
```

The folder name `exp-01` has a hyphen, so `import experiment.exp-01` is a
syntax error — put the directory on `sys.path` as above.

**Download once, not every session.** `/kaggle/working` is wiped when a session
ends. Run this in a CPU notebook, hit *Save Version*, then in your training
notebook use *Add Data → Notebook Output*. It mounts read-only under
`/kaggle/input/` with no download at all.

## Locally

```bash
python download_schiebinger.py                        # -> ./data
python download_schiebinger.py --dest ./data --extract
python download_schiebinger.py --manifest             # also filelist.txt
```

## API

```python
from download_schiebinger import fetch, extract, fetch_manifest
tar = fetch(dest="./data", workers=12)
extract(tar)                                  # -> ./data/GSE122662/

from parallel_download import download
download(any_url, "out.bin", workers=8)
```

## Notes

Standard library only — nothing to pip install.

This is the **raw** archive: per-sample CellRanger output, unnormalized, no
cross-sample gene harmonization. The processed matrix the WOT/scNODE scripts
expect (`ExprMatrix.h5ad` + `cell_days.txt`) is published only via Google Drive
and needs `gdown`; it is not handled here.
