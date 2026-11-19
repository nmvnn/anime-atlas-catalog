#!/usr/bin/env python3
"""Build the compact Anime Atlas search catalogue.

Usage: python3 scripts/build-catalog.py <source-dir> [output-dir]

Sources (all permit commercial use with attribution):
  <source-dir>/manami.json     anime-offline-database, ODbL-1.0 (required)
  <source-dir>/wikidata.json   {"<mal id>": {"en","ja","uk","ru"}} labels from Wikidata, CC0 (optional)
  web/data/catalog-aliases.json  our own alias dataset

No AniDB data is used: its terms are non-commercial. The derived database is distributed under ODbL-1.0.
"""
from pathlib import Path
import datetime, hashlib, json, re, sys

root = Path(__file__).resolve().parents[1]
source = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else root / 'web/public/catalog'

db = json.loads((source / 'manami.json').read_text(encoding='utf-8'))
wikidata_file = source / 'wikidata.json'
wikidata = json.loads(wikidata_file.read_text(encoding='utf-8')) if wikidata_file.exists() else {}

providers = [('mal', r'myanimelist.net/anime/(\d+)'), ('anidb', r'anidb.net/anime/(\d+)'), ('kitsu', r'kitsu.(?:app|io)/anime/(\d+)'), ('anilist', r'anilist.co/anime/(\d+)')]
KANA = re.compile(r'[぀-ヿㇰ-ㇿ]')
FORMATS = {'TV': 'series', 'MOVIE': 'movie', 'OVA': 'ova', 'ONA': 'ova', 'SPECIAL': 'special'}


def clean_names(names):
    return list(dict.fromkeys(n.strip()[:500] for n in names if n and n.strip()))[:100]


rows = []
for item in db['data']:
    ids = []
    for provider, pattern in providers:
        for url in item['sources']:
            match = re.search(pattern, url)
            if match:
                ids.append(provider + ':' + match[1])
    primary = ids[0] if ids else 'aod:' + hashlib.sha256(item['sources'][0].encode()).hexdigest()[:20]
    mal = next((x.split(':')[1] for x in ids if x.startswith('mal:')), None)
    labels = wikidata.get(mal, {}) if mal else {}
    aliases = clean_names([item['title']] + item.get('synonyms', []) + [labels.get(k, '') for k in ('en', 'ja', 'uk', 'ru')])
    rows.append({
        'key': primary, 'ids': ids, 'title': item['title'],
        'uk': labels.get('uk', ''), 'ru': labels.get('ru', ''), 'en': labels.get('en', ''),
        # Original (Japanese) title: Wikidata label, else the first alias written with kana.
        'ja': labels.get('ja', '') or next((a for a in aliases if KANA.search(a)), ''),
        'aliases': aliases, 'format': FORMATS.get(item['type'], 'unknown'),
        'year': item.get('animeSeason', {}).get('year'), 'episodes': item.get('episodes'), 'poster': item.get('picture', ''),
        'sourceUrl': next((u for u in item['sources'] if 'myanimelist.net/anime/' in u), item['sources'][0]),
        'genres': item.get('tags', [])[:6]})

by_id = {identifier: row for row in rows for identifier in row['ids'] + [row['key']]}
# Public catalogue aliases come from our explicit alias dataset, never from a personal library.
for identifier, override in json.loads((root / 'web/data/catalog-aliases.json').read_text(encoding='utf-8')).items():
    row = by_id.get(identifier)
    if not row:
        continue
    for lang in ['uk', 'ru']:
        if lang in override:
            row[lang] = override[lang]
    row['aliases'] = clean_names(row['aliases'] + override.get('aliases', []))
assert len({r['key'] for r in rows}) == len(rows)

out.mkdir(parents=True, exist_ok=True)
build_date = datetime.date.today()
payload = {'schema': 'anime-atlas-catalog', 'version': int(build_date.strftime('%Y%m%d')), 'metadataDate': db['lastUpdate'],
           'titlesRetrieved': build_date.isoformat(), 'license': 'ODbL-1.0',
           'sources': ['anime-offline-database (ODbL-1.0)', 'Wikidata (CC0)'], 'records': rows}
search_bytes = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
(out / 'search.json').write_bytes(search_bytes)
# about.json is the small file the app reads first: it carries the version and the checksum of search.json.
about = {k: v for k, v in payload.items() if k != 'records'} | {
    'entries': len(rows), 'ukrainianTitles': sum(bool(r['uk']) for r in rows), 'russianTitles': sum(bool(r['ru']) for r in rows),
    'englishTitles': sum(bool(r['en']) for r in rows), 'originalTitles': sum(bool(r['ja']) for r in rows),
    'file': 'search.json', 'bytes': len(search_bytes), 'sha256': hashlib.sha256(search_bytes).hexdigest()}
(out / 'about.json').write_text(json.dumps(about, ensure_ascii=False, indent=2), encoding='utf-8')
print((out / 'about.json').read_text(encoding='utf-8'))
