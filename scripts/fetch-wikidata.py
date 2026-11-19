#!/usr/bin/env python3
"""Fetch English/Japanese/Ukrainian/Russian labels of anime from Wikidata (CC0) keyed by MyAnimeList id.
Usage: python3 scripts/fetch-wikidata.py <output.json>
Exit code 1 when Wikidata cannot be reached: the catalogue build then simply runs without these labels."""
import json, re, sys, time, urllib.parse, urllib.request

QUERY = '''SELECT ?mal ?en ?ja ?uk ?ru WHERE {
  ?item wdt:P4086 ?mal .
  OPTIONAL { ?item rdfs:label ?en FILTER(LANG(?en) = "en") }
  OPTIONAL { ?item rdfs:label ?ja FILTER(LANG(?ja) = "ja") }
  OPTIONAL { ?item rdfs:label ?uk FILTER(LANG(?uk) = "uk") }
  OPTIONAL { ?item rdfs:label ?ru FILTER(LANG(?ru) = "ru") }
}'''
URL = 'https://query.wikidata.org/sparql?format=json&query=' + urllib.parse.quote(QUERY)
AGENT = 'anime-atlas-catalog/1.0 (weekly catalogue build; https://github.com/nmvnn/anime-atlas-catalog)'
# Wikipedia-style disambiguation suffixes are not part of the title: "Назва (аніме)", "Title (season 2)".
SUFFIX = re.compile(r'\s*\((?:аніме|аниме|anime|[^)]*(?:сезон|season)[^)]*)\)\s*$', re.I)


def fetch():
    for attempt in range(3):
        try:
            request = urllib.request.Request(URL, headers={'User-Agent': AGENT, 'Accept': 'application/sparql-results+json'})
            with urllib.request.urlopen(request, timeout=150) as response:
                return json.load(response)
        except Exception as error:  # network or query timeout: retry
            print('attempt', attempt + 1, 'failed:', error, file=sys.stderr)
            time.sleep(20 * (attempt + 1))
    return None


def main():
    data = fetch()
    if not data:
        sys.exit(1)
    labels = {}
    for row in data['results']['bindings']:
        entry = labels.setdefault(row['mal']['value'], {})
        for field in ('en', 'ja', 'uk', 'ru'):
            value = row.get(field, {}).get('value', '').strip()
            value = SUFFIX.sub('', value) if value else ''
            if value and not entry.get(field):  # first non-empty label wins
                entry[field] = value
    Path = __import__('pathlib').Path
    Path(sys.argv[1]).write_text(json.dumps(labels, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print('wikidata labels for', len(labels), 'anime')


if __name__ == '__main__':
    main()
