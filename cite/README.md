# cite

Citation normalizer for WG21 papers. Reads markdown papers, checks citation integrity, renumbers to body-first-appearance order, canonicalizes URLs, and optionally auto-fixes all detected issues.

## Usage

```
python cite.py <papers...> [options]
```

Accepts one or more files or directories. When given a directory, recursively processes all `.md` files (skipping hidden dirs like `.git/`, `.cache/`, `__pycache__/`). Files without a References section are silently skipped.

### Options

- `--fix` - Auto-fix all detectable issues (mutually exclusive with `--check`)
- `--dry-run` - Print rewritten content to stdout; do not modify the file
- `--check` - Exit 1 if `--fix` would change the file (CI mode)
- `--config <path>` - Path to YAML config (auto-discovered from paper dir or script dir)
- `--no-resolve` - Skip HTTP URL resolution (offline mode)
- `--no-guess` - Do not construct URLs for papers not in the wg21.link index

### Examples

```bash
# Fix a single paper
python cite/cite.py source/04-april/d4035-escape-hatches.md

# Auto-fix all issues
python cite/cite.py source/04-april/d4035-escape-hatches.md --fix

# Process all papers in a directory
python cite/cite.py source/

# Process multiple files
python cite/cite.py source/04-april/d4035-escape-hatches.md source/01-jan/d4007-*.md

# Preview changes without writing
python cite/cite.py source/04-april/d4035-escape-hatches.md --dry-run

# CI check
python cite/cite.py source/ --check

# Offline mode (skip wg21.link resolution + mailing index fetch)
python cite/cite.py source/04-april/d4035-escape-hatches.md --no-resolve
```

## Three-pass architecture

1. **Scan** (per file) - Parse file, extract citations, parse refs, find issues. No network, no side effects.
2. **Resolve** (batched) - Resolve wg21.link URLs, fetch mailing index metadata. Deduplicates across all files.
3. **Write** (per file) - Apply fixes, renumber, reorder. Pure transform.

This means `--check` only runs scan (+ resolve if needed), and `--no-resolve` skips pass 2 entirely. URL resolution and mailing index fetches happen once across a multi-file batch.

## What it checks

1. **Citation ordering** - `<sup>[N]</sup>` renumbered to body-first-appearance order
2. **Orphan references** - reference entries with no body citation
3. **Missing references** - body citations with no reference entry
4. **Uncited links** - body hyperlinks without a trailing `<sup>[N]</sup>`
5. **wg21.link URLs** - replaced with resolved open-std.org canonical URLs
6. **Unversioned paper numbers** - bare `P1234` without `R0`/`R1` suffix
7. **Malformed citations** - compound `<sup>[1,2]</sup>` that should be split
8. **Title mismatches** - reference title vs mailing index title
9. **Reference format** - `N. text` (Format B) flagged, should be `[N] text` (IEEE)
10. **Heading level** - `# References` (h1) flagged, should be `## References` (h2)

## Auto-fix behavior

**Always applied** (without `--fix`):
- Citation renumbering (body + references)
- Reference entry reordering
- wg21.link to open-std.org URL replacement

**With `--fix`** (additional operations):
- Demote `# References` to `## References`
- Normalize `N. text` to `[N] text` (IEEE format)
- Remove orphan reference entries
- Add `<sup>[N]</sup>` to uncited links + create reference entries
- Resolve unversioned paper numbers via refs or HTTP
- Create missing reference entries from mailing index metadata
- Fix title mismatches from mailing index (skips bad mailing data like bare doc numbers)
- Strip redundant trailing URLs from refs that already have inline links
- Wrap bare URLs in refs as markdown links
- Ensure blank line between consecutive reference entries

Fix operations run in a specific order: heading demotion, format normalization, orphan removal, missing ref stubs, uncited link citations, unversioned paper resolution, title mismatch correction, URL cleanup, entry spacing, then renumber/reorder.

## Paper index

The tool uses the `wg21.link` paper index (`https://wg21.link/index.json`) for paper metadata (title, authors, date) and wg21.link URL resolution. This covers 28,000+ entries including every revision of every WG21 paper, CWG/EWG/LWG issues, and standing documents.

This enables:
- Complete reference entries for WG21 papers (not just stubs)
- Title mismatch detection (titles are correct for all papers including old N-papers)
- Instant wg21.link resolution without per-URL HTTP requests

**Freshness:** The tool sends a HEAD request to check `Last-Modified` and only re-downloads the full index when the server copy is newer. Falls back to the cached copy when offline.

**Constructed URLs:** Papers not in the index (unpublished or pre-publication) get a deterministically constructed `open-std.org` URL from the paper number and current year. This is reliable for the author's own papers (you know the year, revision, and that the paper will be published). For foreign papers, the year or extension might be wrong - use `--no-guess` to disable. Constructed URLs are logged to stderr and summarized at the end of each run.

Non-ASCII characters in metadata (author names with diacriticals) are converted to HTML entities: named where available (e.g. `&eacute;`), decimal numeric otherwise (e.g. `&#322;`).

## Config file

Auto-discovered from the first paper's directory, then the script directory. Override with `--config`. YAML format:

```yaml
exempt_sections:
  - Disclosure
  - Acknowledgements

exempt_links:
  - "https://github.com/cppalliance/corosio*"
  - "https://github.com/cppalliance/capy*"
  - "https://creativecommons.org/*"

exempt_orphans: []
```

- `exempt_sections` - section names where uncited links are not flagged
- `exempt_links` - URL glob patterns for links that are never flagged as uncited
- `exempt_orphans` - glob patterns for reference entry text allowed to be orphaned (e.g. `*github.com/cppalliance*`)

All keys are optional. Missing keys default to empty lists.

## Exit codes

- `0` - success (or `--check` found nothing to change)
- `1` - `--check` found changes needed
- `2` - usage error (bad config, missing file, `--fix` + `--check`)

## Caches

- `.cache/index.json` - wg21.link paper index (28k+ entries, fetched on demand)

The entire `.cache/` directory is git-ignored. On first run, `index.json` is downloaded automatically. Subsequent runs check freshness via a HEAD request and only re-download when the server file has changed.

## Reference format

The tool enforces IEEE-style `[N]` references (Format A):

```
[1] [C++ Working Draft](https://eel.is/c++draft/) - description
```

Format B (`N. text`) entries are detected during scan and automatically converted to Format A with `--fix`. New entries are always emitted as Format A.

## Tests

```bash
cd cite && python -m pytest tests/ -v
```
