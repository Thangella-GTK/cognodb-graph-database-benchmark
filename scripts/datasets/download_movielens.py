#!/usr/bin/env python3
"""Download and extract MovieLens 100k dataset using stdlib only.
Usage: python download_movielens.py <url> <out-zip> <dest-dir>
"""
import sys
from pathlib import Path
import urllib.request
import shutil
import zipfile


def download(url, out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f'Downloading {url} -> {out}')
    with urllib.request.urlopen(url) as r, open(out, 'wb') as f:
        shutil.copyfileobj(r, f)


def extract(zip_path, dest):
    zip_path = Path(zip_path)
    dest = Path(dest)
    print(f'Extracting {zip_path} -> {dest}')
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(dest)


def main():
    if len(sys.argv) < 4:
        print('Usage: download_movielens.py <url> <out-zip> <dest-dir>')
        sys.exit(1)
    url = sys.argv[1]
    out_zip = sys.argv[2]
    dest = sys.argv[3]
    download(url, out_zip)
    extract(out_zip, dest)
    print('Done')


if __name__ == '__main__':
    main()
