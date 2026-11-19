# Anime Atlas catalogue

Search catalogue for the Anime Atlas Android app: about 44 000 titles with Ukrainian, Russian,
English and original (Japanese) names, formats, years, episode counts and cover links.

Privacy policy: privacy.html. Rebuilt automatically every week by GitHub Actions and published through GitHub Pages:

- `about.json` – small file the app reads first (version, entry count, size, SHA-256).
- `search.json` – the catalogue itself. The app verifies its checksum before using it.

## Data and licence

Derived from [anime-offline-database](https://github.com/manami-project/anime-offline-database)
(ODbL-1.0) and [Wikidata](https://www.wikidata.org) labels (CC0). The derived database is published under ODbL-1.0:
attribution is required and changes must be shared under the same licence. No AniDB data is used.

## First-time setup (once)

1. Create a public repository and push this folder to it.
2. Settings → Pages → Source: **GitHub Actions**.
3. Actions → *Build and publish catalogue* → **Run workflow**.
4. The catalogue appears at `https://<user>.github.io/<repo>/about.json`.
