#!/usr/bin/env python3
"""Self-test for build-catalog.py on tiny synthetic sources (no network, no private data).
Checks the English/original title fields, that no AniDB data can leak in, and the about.json contract the app relies on."""
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
MANAMI = {'lastUpdate': '2026-07-04', 'data': [
    {'title': 'Cowboy Bebop', 'type': 'TV', 'episodes': 26, 'animeSeason': {'year': 1998}, 'picture': '',
     'sources': ['https://myanimelist.net/anime/1', 'https://anidb.net/anime/23'], 'synonyms': ['Bebop'], 'tags': ['action']},
    {'title': 'Only Manami', 'type': 'MOVIE', 'episodes': 1, 'animeSeason': {}, 'picture': '',
     'sources': ['https://myanimelist.net/anime/999'], 'synonyms': ['オンリー マナミ'], 'tags': []},
]}
WIKIDATA = {'1': {'en': 'Cowboy Bebop', 'ja': 'カウボーイビバップ', 'uk': 'Ковбой Бібоп', 'ru': 'Ковбой Бибоп'}}


def build(src, out):
    subprocess.run([sys.executable, str(root / 'scripts/build-catalog.py'), str(src), str(out)], check=True, stdout=subprocess.DEVNULL)
    return (out / 'search.json').read_bytes(), json.loads((out / 'about.json').read_text(encoding='utf-8'))


with tempfile.TemporaryDirectory() as tmp:
    src, out = Path(tmp) / 'src', Path(tmp) / 'out'
    src.mkdir()
    (src / 'manami.json').write_text(json.dumps(MANAMI), encoding='utf-8')
    (src / 'wikidata.json').write_text(json.dumps(WIKIDATA, ensure_ascii=False), encoding='utf-8')
    # A stray AniDB dump or previous catalogue in the source folder must be ignored completely.
    (src / 'anidb.xml.gz').write_bytes(b'not used')
    (src / 'previous.json').write_text('{"records":[{"key":"anidb:5000","uk":"leak"}]}', encoding='utf-8')
    search_bytes, about = build(src, out)
    rows = {r['key']: r for r in json.loads(search_bytes)['records']}
    bebop = rows['mal:1']
    assert (bebop['en'], bebop['ja'], bebop['uk'], bebop['ru']) == ('Cowboy Bebop', 'カウボーイビバップ', 'Ковбой Бібоп', 'Ковбой Бибоп'), bebop
    assert rows['mal:999']['en'] == '' and rows['mal:999']['ja'] == 'オンリー マナミ', rows['mal:999']  # ja falls back to a kana alias
    assert 'anidb:5000' not in rows and 'leak' not in search_bytes.decode('utf-8') and len(rows) == 2
    assert about['entries'] == 2 and about['englishTitles'] == 1 and about['originalTitles'] == 2
    assert about['sha256'] == hashlib.sha256(search_bytes).hexdigest() and about['bytes'] == len(search_bytes)
    assert about['schema'] == 'anime-atlas-catalog' and isinstance(about['version'], int) and about['file'] == 'search.json'
    assert 'Wikidata (CC0)' in about['sources']

# Without Wikidata the build still works (names fall back to manami titles and aliases).
with tempfile.TemporaryDirectory() as tmp:
    src, out = Path(tmp) / 'src', Path(tmp) / 'out'
    src.mkdir()
    (src / 'manami.json').write_text(json.dumps(MANAMI), encoding='utf-8')
    search_bytes, about = build(src, out)
    rows = {r['key']: r for r in json.loads(search_bytes)['records']}
    assert rows['mal:1']['en'] == '' and rows['mal:1']['uk'] == '' and len(rows) == 2
print('catalog build test passed')
