#!/usr/bin/env python3
"""Prepare nodes and relationships CSVs from MovieLens 100k files.
Usage: python loader.py <extracted-dir> <out-data-dir>
"""
import sys
from pathlib import Path
import csv


def prepare_movielens(extracted_dir, out_dir):
    extracted_dir = Path(extracted_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    u_data = extracted_dir / 'ml-100k' / 'u.data'
    u_item = extracted_dir / 'ml-100k' / 'u.item'
    if not u_data.exists() or not u_item.exists():
        print('Expected MovieLens files under', extracted_dir / 'ml-100k')
        return

    # Load movies
    movies = {}
    with open(u_item, encoding='latin-1') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) < 2:
                continue
            mid = parts[0]
            title = parts[1]
            movies[mid] = title

    # Write nodes and edges CSVs
    nodes_path = out_dir / 'nodes.csv'
    edges_path = out_dir / 'ratings.csv'

    users_seen = set()
    with open(edges_path, 'w', newline='', encoding='utf-8') as ef:
        w = csv.writer(ef)
        w.writerow(['user_id', 'movie_id', 'rating', 'timestamp'])
        with open(u_data, encoding='latin-1') as df:
            for line in df:
                uid, mid, rating, ts = line.strip().split('\t')
                users_seen.add(uid)
                w.writerow([uid, mid, rating, ts])

    with open(nodes_path, 'w', newline='', encoding='utf-8') as nf:
        w = csv.writer(nf)
        w.writerow(['id', 'type', 'title'])
        for uid in sorted(users_seen):
            w.writerow([f'u{uid}', 'user', ''])
        for mid, title in movies.items():
            w.writerow([f'm{mid}', 'movie', title])

    print('Wrote', nodes_path, 'and', edges_path)


def main():
    if len(sys.argv) < 3:
        print('Usage: loader.py <extracted-dir> <out-data-dir>')
        sys.exit(1)
    prepare_movielens(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    main()
